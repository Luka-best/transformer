"""
perceiver.py Generic interface to various configurations of the Perceiver Resampler, that simply takes in a series of
(potentially time-indexed) contextual embeddings, and "resamples" (compresses) them down to a pre-specified number of
latents! Note that the Perceiver in general resamples based solely off the *long-range* context; there's a nice
opportunity here to prime the Perceiver Resampler with say a single layer's worth of language embeddings (the target
domain), and use that to softly "retrieve & compress" what we need --> this would be a novel contribution we should
explore. References:
    - DeepMind's Flamingo: https://www.deepmind.com/blog/tackling-multiple-tasks-with-a-single-visual-language-model
    - Code borrowed w/ love from: https://github.com/lucidrains/flamingo-pytorch
"""
from typing import Optional, Tuple

import torch
import torch.nn as nn


class PerceiverResampler(nn.Module):
    def __init__(self, config, embed_dim: int, depth: int, n_heads: int, head_dim: int, n_latents: int) -> None:
        """
        Instantiates a Perceiver Resampler that operates over a sequence of embeddings (say from a ResNet or ViT or
        MAE) of a given dimension, performs `depth` blocks of cross-attention with a fixed `n_latents` inputs, then
        returns a Tensor of shape [bsz, n_latents, embed_dim]. :param embed_dim: Dimensionality of embeddings being fed
        to the Perceiver Resampler (also dimensionality of
                          latent embeddings *returned* by the Perceiver Resampler. Could be e.g., VIT embed_dim, ResNet
                          pool dim, and so on.

        Args:
            depth: Depth of the Perceiver Resampler (Transformer w/ cross attention). Should be shallow (< 3).
            n_heads: Number of heads in each Transformer block (for multi-headed self-attention).
            head_dim: Dimensionality of each head projection in the Transformer block.
            n_latents: Number of latent embeddings to resample ("compress") the input sequence to (usually < 128).
        """
        super().__init__()
        self.embed_dim, self.n_heads, self.head_dim, self.n_latents = embed_dim, n_heads, head_dim, n_latents
        self.qk_layer_norms = config.qk_layer_norms_perceiver

        # Create Latents for Perceiver
        self.latents = nn.Parameter(torch.randn(self.n_latents, self.embed_dim), requires_grad=True)

        self.intermediate_dim = (
            self.embed_dim * 4 if not hasattr(config, "vision_embed_dim") else config.vision_embed_dim * 4
        )
        # Create Transformer Blocks
        self.blocks = nn.ModuleList(
            [
                nn.ModuleList(
                    [
                        PerceiverAttention(self.embed_dim, self.n_heads, self.head_dim, self.qk_layer_norms),
                        MLP(self.intermediate_dim, config),
                    ]
                )
                for _ in range(depth)
            ]
        )
        self.layer_norm = nn.LayerNorm(self.embed_dim)

    def forward(self, context: torch.Tensor) -> torch.Tensor:
        """Resample arbitrary length context & *compress* down to self.n_latents latent embeddings"""
        # einsum.repeat(self.latents, "seq embed -> bsz seq embed", bsz=context.shape[0])
        latents = self.latents.repeat(context.shape[0], 1, 1)

        # Feed through Perceiver Attention blocks...
        for attn, ff in self.blocks:
            latents = attn(context, latents) + latents
            latents = ff(latents) + latents

        return self.layer_norm(latents)


class PerceiverAttention(nn.Module):
    def __init__(self, embed_dim: int, n_heads: int, head_dim: int, qk_layer_norms: bool) -> None:
        """Perceiver Cross-Attention Module --> let long-form inputs be `context`, resampled embeddings be `latents`"""
        super().__init__()
        self.embed_dim, self.n_heads, self.head_dim = embed_dim, n_heads, head_dim
        self.qk_layer_norms = qk_layer_norms
        # Normalization & Scaling
        self.context_layer_norm = nn.LayerNorm(self.embed_dim)
        self.latents_layer_norm = nn.LayerNorm(self.embed_dim)
        if self.qk_layer_norms:
            self.q_layer_norm = nn.LayerNorm(self.head_dim)
            self.k_layer_norm = nn.LayerNorm(self.head_dim)

        self.qk_scale = self.head_dim**-0.5

        # Q, K, V Projection (no bias -- detail from Perceiver/Flamingo Papers).
        self.q_proj = nn.Linear(self.embed_dim, self.n_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(self.embed_dim, self.n_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(self.embed_dim, self.n_heads * self.head_dim, bias=False)

        self.output_proj = nn.Linear(self.n_heads * self.head_dim, embed_dim, bias=False)

    def forward(self, context: torch.Tensor, latents: torch.Tensor) -> torch.Tensor:
        """
        Runs Perceiver Self-Attention, with special (context, latents) appended along the `seq` dimension!

        Args:
            context: Tensor of shape [bsz, seq, embed_dim] representing long-form context to resample.
            latents: Tensor of shape [bsz, n_latents, embed_dim] representing fixed length latents to compress to.

        Returns: Tensor of shape [bsz, n_latents, embed_dim] representing attention over latents w/ cross from context.
        """
        context = self.context_layer_norm(context)
        latents = self.latents_layer_norm(latents)
        batch_size, seq_length, embed_dim = context.shape[:3]

        # Query, Key, Value Projections --> Note that in Flamingo, latents are *concatenated* with context prior to attn!
        #   Note: This results in queries w/ `seq = n_latents`, and keys, values with `seq = len(context) + n_latents`
        q = self.q_proj(latents)
        k = self.k_proj(torch.cat([context, latents], dim=-2))
        v = self.v_proj(torch.cat([context, latents], dim=-2))

        # Multiheaded Self-Attention w/ stable softmax (subtract per-row max -- `amax` -- before softmax call)
        #   =>> `attn` should be a 2D matrix of shape [n_latents x (context + n_latents)]
        # einsum.rearrange(x, "bsz seq (heads embed) -> bsz heads seq embed", heads=self.n_heads)
        q, k, v = [x.reshape(batch_size, x.shape[1], self.n_heads, self.head_dim).transpose(1, 2) for x in (q, k, v)]

        if self.qk_layer_norms:
            q = self.q_layer_norm(q)
            k = self.k_layer_norm(k)

        scores = torch.einsum("... i d, ... j d -> ... i j", q * self.qk_scale, k)
        stabilized_scores = scores - (scores.amax(dim=-1, keepdim=True).detach())
        attn = stabilized_scores.softmax(dim=-1)

        # Attend & project back to output...
        resampled = torch.einsum("... i j, ... j d -> ... i d", attn, v)
        # einsum.rearrange(resampled, "bsz heads seq embed -> bsz seq (heads embed)", heads=self.n_heads)
        return self.output_proj(resampled.transpose(1, 2).flatten(-2))


class MLP(nn.Module):
    def __init__(self, intermediate_size, config):
        """Simple MLP block with intermediate_size and embedding size"""
        super().__init__()
        self.embed_dim = config.vision_embed_dim
        self.ln = nn.LayerNorm(self.embed_dim)
        self.fc = nn.Linear(self.embed_dim, intermediate_size, bias=False)
        self.act = nn.ReLU()
        self.c_proj = nn.Linear(intermediate_size, self.embed_dim, bias=False)

    def forward(self, hidden_states: Optional[Tuple[torch.FloatTensor]]) -> torch.FloatTensor:
        hidden_states = self.ln(hidden_states)
        hidden_states = self.fc(hidden_states)
        hidden_states = self.act(hidden_states)
        hidden_states = self.c_proj(hidden_states)

        return hidden_states
