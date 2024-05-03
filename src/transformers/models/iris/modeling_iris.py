# coding=utf-8
# Copyright 2024 Transformers are Sample-Efficient World Models(IRIS) paper authors and The HuggingFace Team The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" PyTorch Iris model."""

import math
from dataclasses import dataclass
from typing import Optional, Tuple, Union, Any

import torch
import torch.utils.checkpoint
from torch import nn
from torch.cuda.amp import autocast

# from ...activations import ACT2FN
from ...modeling_utils import PreTrainedModel
from ...pytorch_utils import Conv1D, find_pruneable_heads_and_indices, prune_conv1d_layer
from ...utils import (
    ModelOutput,
    add_start_docstrings,
    add_start_docstrings_to_model_forward,
    logging,
    replace_return_docstrings,
)
from .configuration_iris import IrisConfig


logger = logging.get_logger(__name__)

_CHECKPOINT_FOR_DOC = "ruffy369/iris-breakout"
_CONFIG_FOR_DOC = "IrisConfig"


IRIS_PRETRAINED_MODEL_ARCHIVE_LIST = [
    "ruffy369/iris-breakout",
    # See all Iris models at https://huggingface.co/models?filter=iris
]




@dataclass
class IrisOutput(ModelOutput):
    """
    Base class for model's outputs that also contains a pooling of the last hidden states.

    Args:
        losses (`Dict[torch.FloatTensor]` of shape `(1,)`):
            Agent's components' total loss (tokenizer, world model and actor critic).
        reconstructed_img (`torch.FloatTensor` of shape `(batch_size, time_steps, num_channels, height, width)`):
            Reconstructed image from input frame 
        action_preds (`torch.FloatTensor` of shape `(batch_size, time_steps, action_dim)`):
            Policy action predictions
        reward_preds (`torch.FloatTensor` of shape `(batch_size, time_steps, 1)`):
            Predicted returns for each state
        epsiode_end (`torch.FloatTensor` of shape `(batch_size, time_steps, 1)`):
            Predicted potential episode termination
        obs_preds (`torch.FloatTensor` of shape `(batch_size, time_Steps, 1)`):
            Predicted tokens for next frame
        hidden_states (`tuple(torch.FloatTensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `torch.FloatTensor` (one for the output of the embeddings + one for the output of each layer) ofshape `(batch_size, sequence_length, hidden_size)`. 
            Hidden-states of the model at the output of each layer plus the initial embedding outputs.
        attentions (`tuple(torch.FloatTensor)`, *optional*, returned when `output_attentions=True` is passed or when `config.output_attentions=True`):
            Tuple of `torch.FloatTensor` (one for each layer) of shape `(batch_size, num_heads, sequence_length, sequence_length)`. 
            Attentions weights after the attention softmax, used to compute the weighted average in the self-attention heads.
    """

    losses: torch.FloatTensor = None
    reconstructed_img: torch.FloatTensor = None
    action_preds: torch.FloatTensor = None
    reward_preds: torch.FloatTensor = None
    epsiode_end: torch.FloatTensor = None
    obs_preds: torch.FloatTensor = None
    hidden_states: Optional[Tuple[torch.FloatTensor]] = None
    attentions: Optional[Tuple[torch.FloatTensor]] = None


class IrisPreTrainedModel(PreTrainedModel):
    """
    An abstract class to handle weights initialization and a simple interface for downloading and loading pretrained
    models.
    """

    config_class = IrisConfig
    base_model_prefix = "iris"
    main_input_name = "observations"
    supports_gradient_checkpointing = True

    def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, (nn.Linear, nn.Embedding)):
            module.weight.data.normal_(mean=0.0, std=self.config.initializer_range) #self.config.initializer_range=0.02 (in original code)
            if isinstance(module, nn.Linear) and module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)

    def _set_gradient_checkpointing(self, module, value=False):
        if isinstance(module, IrisModel):
            module.gradient_checkpointing = value



IRIS_START_DOCSTRING = r"""
    This model is a PyTorch [torch.nn.Module](https://pytorch.org/docs/stable/nn.html#torch.nn.Module) sub-class. Use
    it as a regular PyTorch Module and refer to the PyTorch documentation for all matter related to general usage and
    behavior.

    Parameters:
        config ([`~IrisConfig`]): Model configuration class with all the parameters of the model.
            Initializing with a config file does not load the weights associated with the model, only the
            configuration. Check out the [`~PreTrainedModel.from_pretrained`] method to load the model weights.
"""

#actor_critic :> inputs: torch.FloatTensor()(B, T, C, H, W), mask_padding: Optional[torch.BoolTensor](same size as inp) = None
#world model:> tokens: torch.LongTensor((B, L(K+1)))(B: batch size, L: timesteps, K: number of tokens), past_keys_values: Optional[KeysValues] = None((n_layers,batch_size, num_heads, max_tokens, head_dim))
#tokenizer:> x(B, T, C, H, W)(main): torch.Tensor, should_preprocess(main): bool = False, should_postprocess(main): bool = False
IRIS_INPUTS_DOCSTRING = r"""
    Args:
        observations (`torch.FloatTensor` of shape `(batch_size, timesteps, num_channels, height, width)`):
            The image observations from real environment in L timesteps (only one frame is used from the environment and 
            rest are imagined in the world model for training)
        actions (`torch.FloatTensor` of shape `(batch_size, timesteps)`):
            The actions from real environment in L timesteps
        rewards (`torch.FloatTensor` of shape `(batch_size, timesteps)`):
            The rewards from real environment in L timesteps
        ends (`torch.IntTensor` of shape `(batch_size, timesteps)`):
            The episode termination booleans from real environment in L timesteps
        mask_padding (`torch.BoolTensor` of shape `(batch_size, 1)`):
            The padding mask for input observations before putting them in encode and decoder
        should_preprocess (`bool`, *optional*):
            If set to `True`, `observations` are preprocessed before being passed to the model when encoding.
        should_postprocess(`bool`, *optional*):
            If set to `True`, `reconstructions` are postprocessed after being passed to the model when decoding.
        output_attentions (`bool`, *optional*):
            Whether or not to return the attentions tensors of all attention layers. See `attentions` under returned
            tensors for more detail.
        output_hidden_states (`bool`, *optional*):
            Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors for
            more detail.
        return_dict (`bool`, *optional*):
            Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
        
        
"""

#CODE BLOCKS REQUIRED FOR THE IRIS MODELS(WIP)
#utils:###################

def configure_optimizer(model, learning_rate, weight_decay, *blacklist_module_names):
    """Credits to https://github.com/karpathy/minGPT"""
    # separate out all parameters to those that will and won't experience regularizing weight decay
    decay = set()
    no_decay = set()
    whitelist_weight_modules = (torch.nn.Linear, torch.nn.Conv1d)
    blacklist_weight_modules = (torch.nn.LayerNorm, torch.nn.Embedding)
    for mn, m in model.named_modules():
        for pn, p in m.named_parameters():
            fpn = '%s.%s' % (mn, pn) if mn else pn  # full param name
            if any([fpn.startswith(module_name) for module_name in blacklist_module_names]):
                no_decay.add(fpn)
            elif 'bias' in pn:
                # all biases will not be decayed
                no_decay.add(fpn)
            elif pn.endswith('weight') and isinstance(m, whitelist_weight_modules):
                # weights of whitelist modules will be weight decayed
                decay.add(fpn)
            elif pn.endswith('weight') and isinstance(m, blacklist_weight_modules):
                # weights of blacklist modules will NOT be weight decayed
                no_decay.add(fpn)

    # validate that we considered every parameter
    param_dict = {pn: p for pn, p in model.named_parameters()}
    inter_params = decay & no_decay
    union_params = decay | no_decay
    assert len(inter_params) == 0, f"parameters {str(inter_params)} made it into both decay/no_decay sets!"
    assert len(param_dict.keys() - union_params) == 0, f"parameters {str(param_dict.keys() - union_params)} were not separated into either decay/no_decay set!"

    # create the pytorch optimizer object
    optim_groups = [
        {"params": [param_dict[pn] for pn in sorted(list(decay))], "weight_decay": weight_decay},
        {"params": [param_dict[pn] for pn in sorted(list(no_decay))], "weight_decay": 0.0},
    ]
    optimizer = torch.optim.AdamW(optim_groups, lr=learning_rate)
    return optimizer

#init weights same as in pRetrained model's __init__()
def init_weights(module):
    if isinstance(module, (nn.Linear, nn.Embedding)):
        module.weight.data.normal_(mean=0.0, std=0.02)
        if isinstance(module, nn.Linear) and module.bias is not None:
            module.bias.data.zero_()
    elif isinstance(module, nn.LayerNorm):
        module.bias.data.zero_()
        module.weight.data.fill_(1.0)


def extract_state_dict(state_dict, module_name):
    return OrderedDict({k.split('.', 1)[1]: v for k, v in state_dict.items() if k.startswith(module_name)})







def compute_lambda_returns(rewards, values, ends, gamma, lambda_):
    assert rewards.ndim == 2 or (rewards.ndim == 3 and rewards.size(2) == 1)
    assert rewards.shape == ends.shape == values.shape, f"{rewards.shape}, {values.shape}, {ends.shape}"  # (B, T, 1)
    t = rewards.size(1)
    lambda_returns = torch.empty_like(values)
    lambda_returns[:, -1] = values[:, -1]
    lambda_returns[:, :-1] = rewards[:, :-1] + ends[:, :-1].logical_not() * gamma * (1 - lambda_) * values[:, 1:]

    last = values[:, -1]
    for i in list(range(t - 1))[::-1]:
        lambda_returns[:, i] += ends[:, i].logical_not() * gamma * lambda_ * last
        last = lambda_returns[:, i]

    return lambda_returns


class LossWithIntermediateLosses:
    def __init__(self, **kwargs):
        self.loss_total = sum(kwargs.values())
        self.intermediate_losses = {k: v.item() for k, v in kwargs.items()}

    def __truediv__(self, value):
        for k, v in self.intermediate_losses.items():
            self.intermediate_losses[k] = v / value
        self.loss_total = self.loss_total / value
        return self


class EpisodeDirManager:
    def __init__(self, episode_dir: Path, max_num_episodes: int) -> None:
        self.episode_dir = episode_dir
        self.episode_dir.mkdir(parents=False, exist_ok=True)
        self.max_num_episodes = max_num_episodes
        self.best_return = float('-inf')

    def save(self, episode: Episode, episode_id: int, epoch: int) -> None:
        if self.max_num_episodes is not None and self.max_num_episodes > 0:
            self._save(episode, episode_id, epoch)

    def _save(self, episode: Episode, episode_id: int, epoch: int) -> None:
        ep_paths = [p for p in self.episode_dir.iterdir() if p.stem.startswith('episode_')]
        assert len(ep_paths) <= self.max_num_episodes
        if len(ep_paths) == self.max_num_episodes:
            to_remove = min(ep_paths, key=lambda ep_path: int(ep_path.stem.split('_')[1]))
            to_remove.unlink()
        episode.save(self.episode_dir / f'episode_{episode_id}_epoch_{epoch}.pt')

        ep_return = episode.compute_metrics().episode_return
        if ep_return > self.best_return:
            self.best_return = ep_return
            path_best_ep = [p for p in self.episode_dir.iterdir() if p.stem.startswith('best_')]
            assert len(path_best_ep) in (0, 1)
            if len(path_best_ep) == 1:
                path_best_ep[0].unlink()
            episode.save(self.episode_dir / f'best_episode_{episode_id}_epoch_{epoch}.pt')


class RandomHeuristic:
    def __init__(self, num_actions):
        self.num_actions = num_actions

    def act(self, obs):
        assert obs.ndim == 4  # (N, H, W, C)
        n = obs.size(0)
        return torch.randint(low=0, high=self.num_actions, size=(n,))
###############################################################################################
#env:


class MessageType(Enum):
    RESET = 0
    RESET_RETURN = 1
    STEP = 2
    STEP_RETURN = 3
    CLOSE = 4


@dataclass
class Message:
    type: MessageType
    content: Optional[Any] = None

    def __iter__(self) -> Iterator:
        return iter(astuple(self))


def child_env(child_id: int, env_fn: Callable, child_conn: Connection) -> None:
    np.random.seed(child_id + np.random.randint(0, 2 ** 31 - 1))
    env = env_fn()
    while True:
        message_type, content = child_conn.recv()
        if message_type == MessageType.RESET:
            obs = env.reset()
            child_conn.send(Message(MessageType.RESET_RETURN, obs))
        elif message_type == MessageType.STEP:
            obs, rew, done, _ = env.step(content)
            if done:
                obs = env.reset()
            child_conn.send(Message(MessageType.STEP_RETURN, (obs, rew, done, None)))
        elif message_type == MessageType.CLOSE:
            child_conn.close()
            return
        else:
            raise NotImplementedError


class MultiProcessEnv(DoneTrackerEnv):
    def __init__(self, env_fn: Callable, num_envs: int, should_wait_num_envs_ratio: float) -> None:
        super().__init__(num_envs)
        self.num_actions = env_fn().env.action_space.n
        self.should_wait_num_envs_ratio = should_wait_num_envs_ratio
        self.processes, self.parent_conns = [], []
        for child_id in range(num_envs):
            parent_conn, child_conn = Pipe()
            self.parent_conns.append(parent_conn)
            p = Process(target=child_env, args=(child_id, env_fn, child_conn), daemon=True)
            self.processes.append(p)
        for p in self.processes:
            p.start()

    def should_reset(self) -> bool:
        return (self.num_envs_done / self.num_envs) >= self.should_wait_num_envs_ratio

    def _receive(self, check_type: Optional[MessageType] = None) -> List[Any]:
        messages = [parent_conn.recv() for parent_conn in self.parent_conns]
        if check_type is not None:
            assert all([m.type == check_type for m in messages])
        return [m.content for m in messages]

    def reset(self) -> np.ndarray:
        self.reset_done_tracker()
        for parent_conn in self.parent_conns:
            parent_conn.send(Message(MessageType.RESET))
        content = self._receive(check_type=MessageType.RESET_RETURN)
        return np.stack(content)

    def step(self, actions: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Any]:
        for parent_conn, action in zip(self.parent_conns, actions):
            parent_conn.send(Message(MessageType.STEP, action))
        content = self._receive(check_type=MessageType.STEP_RETURN)
        obs, rew, done, _ = zip(*content)
        done = np.stack(done)
        self.update_done_tracker(done)
        return np.stack(obs), np.stack(rew), done, None

    def close(self) -> None:
        for parent_conn in self.parent_conns:
            parent_conn.send(Message(MessageType.CLOSE))
        for p in self.processes:
            p.join()
        for parent_conn in self.parent_conns:
            parent_conn.close()



class SingleProcessEnv(DoneTrackerEnv):
    def __init__(self, env_fn):
        super().__init__(num_envs=1)
        self.env = env_fn()
        self.num_actions = self.env.action_space.n

    def should_reset(self) -> bool:
        return self.num_envs_done == 1

    def reset(self) -> np.ndarray:
        self.reset_done_tracker()
        obs = self.env.reset()
        return obs[None, ...]

    def step(self, action) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Any]:
        obs, reward, done, _ = self.env.step(action[0])  # action is supposed to be ndarray (1,)
        done = np.array([done])
        self.update_done_tracker(done)
        return obs[None, ...], np.array([reward]), done, None

    def render(self) -> None:
        self.env.render()

    def close(self) -> None:
        self.env.close()
###############################################################################
#collector

class Collector:
    def __init__(self, env: Union[SingleProcessEnv, MultiProcessEnv], dataset: EpisodesDataset, episode_dir_manager: EpisodeDirManager) -> None:
        self.env = env
        self.dataset = dataset
        self.episode_dir_manager = episode_dir_manager
        self.obs = self.env.reset()
        self.episode_ids = [None] * self.env.num_envs
        self.heuristic = RandomHeuristic(self.env.num_actions)

    @torch.no_grad()
    def collect(self, agent: Agent, epoch: int, epsilon: float, should_sample: bool, temperature: float, burn_in: int, *, num_steps: Optional[int] = None, num_episodes: Optional[int] = None):
        assert self.env.num_actions == agent.world_model.act_vocab_size
        assert 0 <= epsilon <= 1

        assert (num_steps is None) != (num_episodes is None)
        should_stop = lambda steps, episodes: steps >= num_steps if num_steps is not None else episodes >= num_episodes

        to_log = []
        steps, episodes = 0, 0
        returns = []
        observations, actions, rewards, dones = [], [], [], []

        burnin_obs_rec, mask_padding = None, None
        if set(self.episode_ids) != {None} and burn_in > 0:
            current_episodes = [self.dataset.get_episode(episode_id) for episode_id in self.episode_ids]
            segmented_episodes = [episode.segment(start=len(episode) - burn_in, stop=len(episode), should_pad=True) for episode in current_episodes]
            mask_padding = torch.stack([episode.mask_padding for episode in segmented_episodes], dim=0).to(agent.device)
            burnin_obs = torch.stack([episode.observations for episode in segmented_episodes], dim=0).float().div(255).to(agent.device)
            burnin_obs_rec = torch.clamp(agent.tokenizer.encode_decode(burnin_obs, should_preprocess=True, should_postprocess=True), 0, 1)

        agent.actor_critic.reset(n=self.env.num_envs, burnin_observations=burnin_obs_rec, mask_padding=mask_padding)
        pbar = tqdm(total=num_steps if num_steps is not None else num_episodes, desc=f'Experience collection ({self.dataset.name})', file=sys.stdout)

        while not should_stop(steps, episodes):

            observations.append(self.obs)
            obs = rearrange(torch.FloatTensor(self.obs).div(255), 'n h w c -> n c h w').to(agent.device)
            act = agent.act(obs, should_sample=should_sample, temperature=temperature).cpu().numpy()

            if random.random() < epsilon:
                act = self.heuristic.act(obs).cpu().numpy()

            self.obs, reward, done, _ = self.env.step(act)

            actions.append(act)
            rewards.append(reward)
            dones.append(done)

            new_steps = len(self.env.mask_new_dones)
            steps += new_steps
            pbar.update(new_steps if num_steps is not None else 0)

            # Warning: with EpisodicLifeEnv + MultiProcessEnv, reset is ignored if not a real done.
            # Thus, segments of experience following a life loss and preceding a general done are discarded.
            # Not a problem with a SingleProcessEnv.

            if self.env.should_reset():
                self.add_experience_to_dataset(observations, actions, rewards, dones)

                new_episodes = self.env.num_envs
                episodes += new_episodes
                pbar.update(new_episodes if num_episodes is not None else 0)

                for episode_id in self.episode_ids:
                    episode = self.dataset.get_episode(episode_id)
                    self.episode_dir_manager.save(episode, episode_id, epoch)
                    metrics_episode = {k: v for k, v in episode.compute_metrics().__dict__.items()}
                    metrics_episode['episode_num'] = episode_id
                    metrics_episode['action_histogram'] = wandb.Histogram(np_histogram=np.histogram(episode.actions.numpy(), bins=np.arange(0, self.env.num_actions + 1) - 0.5, density=True))
                    to_log.append({f'{self.dataset.name}/{k}': v for k, v in metrics_episode.items()})
                    returns.append(metrics_episode['episode_return'])

                self.obs = self.env.reset()
                self.episode_ids = [None] * self.env.num_envs
                agent.actor_critic.reset(n=self.env.num_envs)
                observations, actions, rewards, dones = [], [], [], []

        # Add incomplete episodes to dataset, and complete them later.
        if len(observations) > 0:
            self.add_experience_to_dataset(observations, actions, rewards, dones)

        agent.actor_critic.clear()

        metrics_collect = {
            '#episodes': len(self.dataset),
            '#steps': sum(map(len, self.dataset.episodes)),
        }
        if len(returns) > 0:
            metrics_collect['return'] = np.mean(returns)
        metrics_collect = {f'{self.dataset.name}/{k}': v for k, v in metrics_collect.items()}
        to_log.append(metrics_collect)

        return to_log

    def add_experience_to_dataset(self, observations: List[np.ndarray], actions: List[np.ndarray], rewards: List[np.ndarray], dones: List[np.ndarray]) -> None:
        assert len(observations) == len(actions) == len(rewards) == len(dones)
        for i, (o, a, r, d) in enumerate(zip(*map(lambda arr: np.swapaxes(arr, 0, 1), [observations, actions, rewards, dones]))):  # Make everything (N, T, ...) instead of (T, N, ...)
            episode = Episode(
                observations=torch.ByteTensor(o).permute(0, 3, 1, 2).contiguous(),  # channel-first
                actions=torch.LongTensor(a),
                rewards=torch.FloatTensor(r),
                ends=torch.LongTensor(d),
                mask_padding=torch.ones(d.shape[0], dtype=torch.bool),
            )
            if self.episode_ids[i] is None:
                self.episode_ids[i] = self.dataset.add_episode(episode)
            else:
                self.dataset.update_episode(self.episode_ids[i], episode)


###############################################################################################################
#WORLD MODEL

class Slicer(nn.Module):
    def __init__(self, max_blocks: int, block_mask: torch.Tensor) -> None:
        super().__init__()
        self.block_size = block_mask.size(0)
        self.num_kept_tokens = block_mask.sum().long().item()
        kept_indices = torch.where(block_mask)[0].repeat(max_blocks)
        offsets = torch.arange(max_blocks).repeat_interleave(self.num_kept_tokens)
        self.register_buffer('indices', kept_indices + block_mask.size(0) * offsets)

    def compute_slice(self, num_steps: int, prev_steps: int = 0) -> torch.Tensor:
        total_steps = num_steps + prev_steps
        num_blocks = math.ceil(total_steps / self.block_size)
        indices = self.indices[:num_blocks * self.num_kept_tokens]
        return indices[torch.logical_and(prev_steps <= indices, indices < total_steps)] - prev_steps

    def forward(self, *args, **kwargs):
        raise NotImplementedError


class Head(Slicer):
    def __init__(self, max_blocks: int, block_mask: torch.Tensor, head_module: nn.Module) -> None:
        super().__init__(max_blocks, block_mask)
        assert isinstance(head_module, nn.Module)
        self.head_module = head_module

    def forward(self, x: torch.Tensor, num_steps: int, prev_steps: int) -> torch.Tensor:
        hidden_states = ()
        x_sliced = x[:, self.compute_slice(num_steps, prev_steps)]  # x is (B, T, E)
        # Add the hidden state to the tuple after Relu activation
        x_sliced_hidden = self.head_module[1](self.head_module[0](x_sliced))
        hidden_states = hidden_states + (x_sliced_hidden,)
        hidden_states = hidden_states+ (self.head_module[2](x_sliced_hidden),)

        return self.head_module(x_sliced), hidden_states


class Embedder(nn.Module):
    def __init__(self, max_blocks: int, block_masks: List[torch.Tensor], embedding_tables: List[nn.Embedding]) -> None:
        super().__init__()
        assert len(block_masks) == len(embedding_tables)
        assert (sum(block_masks) == 1).all()  # block mask are a partition of a block
        self.embedding_dim = embedding_tables[0].embedding_dim
        assert all([e.embedding_dim == self.embedding_dim for e in embedding_tables])
        self.embedding_tables = embedding_tables
        self.slicers = [Slicer(max_blocks, block_mask) for block_mask in block_masks]

    def forward(self, tokens: torch.Tensor, num_steps: int, prev_steps: int) -> torch.Tensor:
        assert tokens.ndim == 2  # x is (B, T)
        output = torch.zeros(*tokens.size(), self.embedding_dim, device=tokens.device)
        for slicer, emb in zip(self.slicers, self.embedding_tables):
            s = slicer.compute_slice(num_steps, prev_steps)
            output[:, s] = emb(tokens[:, s])
        return output

#NETSSS
class Encoder(nn.Module):
    def __init__(self, config: EncoderDecoderConfig) -> None:
        super().__init__()
        self.config = config
        self.num_resolutions = len(config.ch_mult)
        temb_ch = 0  # timestep embedding #channels

        # downsampling
        self.conv_in = torch.nn.Conv2d(config.in_channels,
                                       config.ch,
                                       kernel_size=3,
                                       stride=1,
                                       padding=1)

        curr_res = config.resolution
        in_ch_mult = (1,) + tuple(config.ch_mult)
        self.down = nn.ModuleList()
        for i_level in range(self.num_resolutions):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_in = config.ch * in_ch_mult[i_level]
            block_out = config.ch * config.ch_mult[i_level]
            for i_block in range(self.config.num_res_blocks):
                block.append(ResnetBlock(in_channels=block_in,
                                         out_channels=block_out,
                                         temb_channels=temb_ch,
                                         dropout=config.dropout))
                block_in = block_out
                if curr_res in config.attn_resolutions:
                    attn.append(AttnBlock(block_in))
            down = nn.Module()
            down.block = block
            down.attn = attn
            if i_level != self.num_resolutions - 1:
                down.downsample = Downsample(block_in, with_conv=True)
                curr_res = curr_res // 2
            self.down.append(down)

        # middle
        self.mid = nn.Module()
        self.mid.block_1 = ResnetBlock(in_channels=block_in,
                                       out_channels=block_in,
                                       temb_channels=temb_ch,
                                       dropout=config.dropout)
        self.mid.attn_1 = AttnBlock(block_in)
        self.mid.block_2 = ResnetBlock(in_channels=block_in,
                                       out_channels=block_in,
                                       temb_channels=temb_ch,
                                       dropout=config.dropout)

        # end
        self.norm_out = Normalize(block_in)
        self.conv_out = torch.nn.Conv2d(block_in,
                                        config.z_channels,
                                        kernel_size=3,
                                        stride=1,
                                        padding=1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, list[torch.Tensor]]:
        temb = None  # timestep embedding

        # downsampling
        hs = [self.conv_in(x)]
        hidden_states = ()
        for i_level in range(self.num_resolutions):
            for i_block in range(self.config.num_res_blocks):
                h = self.down[i_level].block[i_block](hs[-1], temb)
                if len(self.down[i_level].attn) > 0:
                    h = self.down[i_level].attn[i_block](h)
                hs.append(h)
                # Add the hidden state to the tuple
                hidden_states = hidden_states + (h,)
            if i_level != self.num_resolutions - 1:
                hs.append(self.down[i_level].downsample(hs[-1]))

        # middle
        h = hs[-1]
        h = self.mid.block_1(h, temb)
        # Add the hidden state to the tuple
        hidden_states = hidden_states + (h,)
        h = self.mid.attn_1(h)
        # Add the hidden state to the tuple
        hidden_states = hidden_states + (h,)
        h = self.mid.block_2(h, temb)
        # Add the hidden state to the tuple
        hidden_states = hidden_states + (h,)

        # end
        h = self.norm_out(h)
        h = nonlinearity(h)
        h = self.conv_out(h)
        return h, hidden_states



class Decoder(nn.Module):
    def __init__(self, config: EncoderDecoderConfig) -> None:
        super().__init__()
        self.config = config
        temb_ch = 0
        self.num_resolutions = len(config.ch_mult)

        # compute in_ch_mult, block_in and curr_res at lowest res
        in_ch_mult = (1,) + tuple(config.ch_mult)
        block_in = config.ch * config.ch_mult[self.num_resolutions - 1]
        curr_res = config.resolution // 2 ** (self.num_resolutions - 1)
        print(f"Tokenizer : shape of latent is {config.z_channels, curr_res, curr_res}.")

        # z to block_in
        self.conv_in = torch.nn.Conv2d(config.z_channels,
                                       block_in,
                                       kernel_size=3,
                                       stride=1,
                                       padding=1)

        # middle
        self.mid = nn.Module()
        self.mid.block_1 = ResnetBlock(in_channels=block_in,
                                       out_channels=block_in,
                                       temb_channels=temb_ch,
                                       dropout=config.dropout)
        self.mid.attn_1 = AttnBlock(block_in)
        self.mid.block_2 = ResnetBlock(in_channels=block_in,
                                       out_channels=block_in,
                                       temb_channels=temb_ch,
                                       dropout=config.dropout)

        # upsampling
        self.up = nn.ModuleList()
        for i_level in reversed(range(self.num_resolutions)):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_out = config.ch * config.ch_mult[i_level]
            for i_block in range(config.num_res_blocks + 1):
                block.append(ResnetBlock(in_channels=block_in,
                                         out_channels=block_out,
                                         temb_channels=temb_ch,
                                         dropout=config.dropout))
                block_in = block_out
                if curr_res in config.attn_resolutions:
                    attn.append(AttnBlock(block_in))
            up = nn.Module()
            up.block = block
            up.attn = attn
            if i_level != 0:
                up.upsample = Upsample(block_in, with_conv=True)
                curr_res = curr_res * 2
            self.up.insert(0, up)  # prepend to get consistent order

        # end
        self.norm_out = Normalize(block_in)
        self.conv_out = torch.nn.Conv2d(block_in,
                                        config.out_ch,
                                        kernel_size=3,
                                        stride=1,
                                        padding=1)

    def forward(self, z: torch.Tensor) -> tuple[torch.Tensor, list[torch.Tensor]]:
        temb = None  # timestep embedding

        # z to block_in
        h = self.conv_in(z)
        hidden_states = ()

        # middle
        h = self.mid.block_1(h, temb)
        # Add the hidden state to the tuple
        hidden_states = hidden_states + (h,)
        h = self.mid.attn_1(h)
        # Add the hidden state to the tuple
        hidden_states = hidden_states + (h,)
        h = self.mid.block_2(h, temb)
        # Add the hidden state to the tuple
        hidden_states = hidden_states + (h,)

        # upsampling
        for i_level in reversed(range(self.num_resolutions)):
            for i_block in range(self.config.num_res_blocks + 1):
                h = self.up[i_level].block[i_block](h, temb)
                # Add the hidden state to the tuple
                hidden_states = hidden_states + (h,)
                if len(self.up[i_level].attn) > 0:
                    h = self.up[i_level].attn[i_block](h)
                    # Add the hidden state to the tuple
                    hidden_states = hidden_states + (h,)
            if i_level != 0:
                h = self.up[i_level].upsample(h)
                # Add the hidden state to the tuple
                hidden_states = hidden_states + (h,)

        # end
        h = self.norm_out(h)
        h = nonlinearity(h)
        h = self.conv_out(h)
        return h, hidden_states



def nonlinearity(x: torch.Tensor) -> torch.Tensor:
    # swish
    return x * torch.sigmoid(x)


def Normalize(in_channels: int) -> nn.Module:
    return torch.nn.GroupNorm(num_groups=32, num_channels=in_channels, eps=1e-6, affine=True)


class Upsample(nn.Module):
    def __init__(self, in_channels: int, with_conv: bool) -> None:
        super().__init__()
        self.with_conv = with_conv
        if self.with_conv:
            self.conv = torch.nn.Conv2d(in_channels,
                                        in_channels,
                                        kernel_size=3,
                                        stride=1,
                                        padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.nn.functional.interpolate(x, scale_factor=2.0, mode="nearest")
        if self.with_conv:
            x = self.conv(x)
        return x


class Downsample(nn.Module):
    def __init__(self, in_channels: int, with_conv: bool) -> None:
        super().__init__()
        self.with_conv = with_conv
        if self.with_conv:
            # no asymmetric padding in torch conv, must do it ourselves
            self.conv = torch.nn.Conv2d(in_channels,
                                        in_channels,
                                        kernel_size=3,
                                        stride=2,
                                        padding=0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.with_conv:
            pad = (0, 1, 0, 1)
            x = torch.nn.functional.pad(x, pad, mode="constant", value=0)
            x = self.conv(x)
        else:
            x = torch.nn.functional.avg_pool2d(x, kernel_size=2, stride=2)
        return x


class ResnetBlock(nn.Module):
    def __init__(self, *, in_channels: int, out_channels: int = None, conv_shortcut: bool = False,
                 dropout: float, temb_channels: int = 512) -> None:
        super().__init__()
        self.in_channels = in_channels
        out_channels = in_channels if out_channels is None else out_channels
        self.out_channels = out_channels
        self.use_conv_shortcut = conv_shortcut

        self.norm1 = Normalize(in_channels)
        self.conv1 = torch.nn.Conv2d(in_channels,
                                     out_channels,
                                     kernel_size=3,
                                     stride=1,
                                     padding=1)
        if temb_channels > 0:
            self.temb_proj = torch.nn.Linear(temb_channels,
                                             out_channels)
        self.norm2 = Normalize(out_channels)
        self.dropout = torch.nn.Dropout(dropout)
        self.conv2 = torch.nn.Conv2d(out_channels,
                                     out_channels,
                                     kernel_size=3,
                                     stride=1,
                                     padding=1)
        if self.in_channels != self.out_channels:
            if self.use_conv_shortcut:
                self.conv_shortcut = torch.nn.Conv2d(in_channels,
                                                     out_channels,
                                                     kernel_size=3,
                                                     stride=1,
                                                     padding=1)
            else:
                self.nin_shortcut = torch.nn.Conv2d(in_channels,
                                                    out_channels,
                                                    kernel_size=1,
                                                    stride=1,
                                                    padding=0)

    def forward(self, x: torch.Tensor, temb: torch.Tensor) -> torch.Tensor:
        h = x
        h = self.norm1(h)
        h = nonlinearity(h)
        h = self.conv1(h)

        if temb is not None:
            h = h + self.temb_proj(nonlinearity(temb))[:, :, None, None]

        h = self.norm2(h)
        h = nonlinearity(h)
        h = self.dropout(h)
        h = self.conv2(h)

        if self.in_channels != self.out_channels:
            if self.use_conv_shortcut:
                x = self.conv_shortcut(x)
            else:
                x = self.nin_shortcut(x)

        return x + h


class AttnBlock(nn.Module):
    def __init__(self, in_channels: int) -> None:
        super().__init__()
        self.in_channels = in_channels

        self.norm = Normalize(in_channels)
        self.q = torch.nn.Conv2d(in_channels,
                                 in_channels,
                                 kernel_size=1,
                                 stride=1,
                                 padding=0)
        self.k = torch.nn.Conv2d(in_channels,
                                 in_channels,
                                 kernel_size=1,
                                 stride=1,
                                 padding=0)
        self.v = torch.nn.Conv2d(in_channels,
                                 in_channels,
                                 kernel_size=1,
                                 stride=1,
                                 padding=0)
        self.proj_out = torch.nn.Conv2d(in_channels,
                                        in_channels,
                                        kernel_size=1,
                                        stride=1,
                                        padding=0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h_ = x
        h_ = self.norm(h_)
        q = self.q(h_)
        k = self.k(h_)
        v = self.v(h_)

        # compute attention
        b, c, h, w = q.shape
        q = q.reshape(b, c, h * w)
        q = q.permute(0, 2, 1)      # b,hw,c
        k = k.reshape(b, c, h * w)  # b,c,hw
        w_ = torch.bmm(q, k)        # b,hw,hw    w[b,i,j]=sum_c q[b,i,c]k[b,c,j]
        w_ = w_ * (int(c) ** (-0.5))
        w_ = torch.nn.functional.softmax(w_, dim=2)

        # attend to values
        v = v.reshape(b, c, h * w)
        w_ = w_.permute(0, 2, 1)   # b,hw,hw (first hw of k, second of q)
        h_ = torch.bmm(v, w_)     # b, c,hw (hw of q) h_[b,c,j] = sum_i v[b,c,i] w_[b,i,j]
        h_ = h_.reshape(b, c, h, w)

        h_ = self.proj_out(h_)

        return x + h_
################################################################
########################3TOKENIZER
class Tokenizer(nn.Module):
    def __init__(self, vocab_size: int, embed_dim: int, encoder: Encoder, decoder: Decoder, with_lpips: bool = True) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.encoder = encoder
        self.pre_quant_conv = torch.nn.Conv2d(encoder.config.z_channels, embed_dim, 1)
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.post_quant_conv = torch.nn.Conv2d(embed_dim, decoder.config.z_channels, 1)
        self.decoder = decoder
        self.embedding.weight.data.uniform_(-1.0 / vocab_size, 1.0 / vocab_size)
        self.lpips = LPIPS().eval() if with_lpips else None

    def __repr__(self) -> str:
        return "tokenizer"

    def forward(self, x: torch.Tensor, should_preprocess: bool = False, should_postprocess: bool = False) -> Tuple[torch.Tensor]:
        outputs, all_hidden_states_enc = self.encode(x, should_preprocess)
        decoder_input = outputs.z + (outputs.z_quantized - outputs.z).detach()
        reconstructions, all_hidden_states_dec = self.decode(decoder_input, should_postprocess)
        return outputs.z, outputs.z_quantized, reconstructions, (all_hidden_states_enc, all_hidden_states_dec)

    def compute_loss(self, batch: Batch, **kwargs: Any) -> LossWithIntermediateLosses:
        assert self.lpips is not None
        observations = self.preprocess_input(rearrange(batch['observations'], 'b t c h w -> (b t) c h w'))
        z, z_quantized, reconstructions = self(observations, should_preprocess=False, should_postprocess=False)

        # Codebook loss. Notes:
        # - beta position is different from taming and identical to original VQVAE paper
        # - VQVAE uses 0.25 by default
        beta = 1.0
        commitment_loss = (z.detach() - z_quantized).pow(2).mean() + beta * (z - z_quantized.detach()).pow(2).mean()

        reconstruction_loss = torch.abs(observations - reconstructions).mean()
        perceptual_loss = torch.mean(self.lpips(observations, reconstructions))

        return LossWithIntermediateLosses(commitment_loss=commitment_loss, reconstruction_loss=reconstruction_loss, perceptual_loss=perceptual_loss)

    def encode(self, x: torch.Tensor, should_preprocess: bool = False) -> TokenizerEncoderOutput:
        if should_preprocess:
            x = self.preprocess_input(x)
        shape = x.shape  # (..., C, H, W)
        x = x.view(-1, *shape[-3:])
        z, all_hidden_states = self.encoder(x)
        z = self.pre_quant_conv(z)
        b, e, h, w = z.shape
        z_flattened = rearrange(z, 'b e h w -> (b h w) e')
        dist_to_embeddings = torch.sum(z_flattened ** 2, dim=1, keepdim=True) + torch.sum(self.embedding.weight**2, dim=1) - 2 * torch.matmul(z_flattened, self.embedding.weight.t())

        tokens = dist_to_embeddings.argmin(dim=-1)
        z_q = rearrange(self.embedding(tokens), '(b h w) e -> b e h w', b=b, e=e, h=h, w=w).contiguous()

        # Reshape to original
        z = z.reshape(*shape[:-3], *z.shape[1:])
        z_q = z_q.reshape(*shape[:-3], *z_q.shape[1:])
        tokens = tokens.reshape(*shape[:-3], -1)

        return TokenizerEncoderOutput(z, z_q, tokens), all_hidden_states

    def decode(self, z_q: torch.Tensor, should_postprocess: bool = False) -> torch.Tensor:
        shape = z_q.shape  # (..., E, h, w)
        z_q = z_q.view(-1, *shape[-3:])
        z_q = self.post_quant_conv(z_q)
        rec, all_hidden_states = self.decoder(z_q)
        rec = rec.reshape(*shape[:-3], *rec.shape[1:])
        if should_postprocess:
            rec = self.postprocess_output(rec)
        return rec, all_hidden_states

    @torch.no_grad()
    def encode_decode(self, x: torch.Tensor, should_preprocess: bool = False, should_postprocess: bool = False) -> torch.Tensor:
        z_q = self.encode(x, should_preprocess).z_quantized
        return self.decode(z_q, should_postprocess)

    def preprocess_input(self, x: torch.Tensor) -> torch.Tensor:
        """x is supposed to be channels first and in [0, 1]"""
        return x.mul(2).sub(1)

    def postprocess_output(self, y: torch.Tensor) -> torch.Tensor:
        """y is supposed to be channels first and in [-1, 1]"""
        return y.add(1).div(2)


class Transformer(nn.Module):
    def __init__(self, config: TransformerConfig) -> None:
        super().__init__()
        self.config = config
        self.drop = nn.Dropout(config.embed_pdrop)
        self.blocks = nn.ModuleList([Block(config) for _ in range(config.num_layers)])
        self.ln_f = nn.LayerNorm(config.embed_dim)

    def generate_empty_keys_values(self, n: int, max_tokens: int) -> KeysValues:
        device = self.ln_f.weight.device  # Assumption that all submodules are on the same device
        return KeysValues(n, self.config.num_heads, max_tokens, self.config.embed_dim, self.config.num_layers, device)

    def forward(self, sequences: torch.Tensor, past_keys_values: Optional[KeysValues] = None) -> torch.Tensor:
        hidden_states = ()
        assert past_keys_values is None or len(past_keys_values) == len(self.blocks)
        #pos and token embeddings to return in hidden states
        x = self.drop(sequences)
        hidden_states = hidden_states + (x,)
        for i, block in enumerate(self.blocks):
            x = block(x, None if past_keys_values is None else past_keys_values[i])
            hidden_states = hidden_states + (x,)

        x = self.ln_f(x)
        hidden_states = hidden_states + (x,)
        return x, hidden_states


class Block(nn.Module):
    def __init__(self, config: TransformerConfig) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(config.embed_dim)
        self.ln2 = nn.LayerNorm(config.embed_dim)
        self.attn = SelfAttention(config)
        self.mlp = nn.Sequential(
            nn.Linear(config.embed_dim, 4 * config.embed_dim),
            nn.GELU(),
            nn.Linear(4 * config.embed_dim, config.embed_dim),
            nn.Dropout(config.resid_pdrop),
        )

    def forward(self, x: torch.Tensor, past_keys_values: Optional[KeysValues] = None) -> torch.Tensor:
        x_attn = self.attn(self.ln1(x), past_keys_values)
        x = x + x_attn
        x = x + self.mlp(self.ln2(x))
        return x


class SelfAttention(nn.Module):
    def __init__(self, config: TransformerConfig) -> None:
        super().__init__()
        assert config.embed_dim % config.num_heads == 0
        assert config.attention in ('causal', 'block_causal')
        self.num_heads = config.num_heads
        self.key = nn.Linear(config.embed_dim, config.embed_dim)
        self.query = nn.Linear(config.embed_dim, config.embed_dim)
        self.value = nn.Linear(config.embed_dim, config.embed_dim)
        self.attn_drop = nn.Dropout(config.attn_pdrop)
        self.resid_drop = nn.Dropout(config.resid_pdrop)
        self.proj = nn.Linear(config.embed_dim, config.embed_dim)

        causal_mask = torch.tril(torch.ones(config.max_tokens, config.max_tokens))
        block_causal_mask = torch.max(causal_mask, torch.block_diag(*[torch.ones(config.tokens_per_block, config.tokens_per_block) for _ in range(config.max_blocks)]))
        self.register_buffer('mask', causal_mask if config.attention == 'causal' else block_causal_mask)

    def forward(self, x: torch.Tensor, kv_cache: Optional[KVCache] = None) -> torch.Tensor:
        B, T, C = x.size()
        if kv_cache is not None:
            b, nh, L, c = kv_cache.shape
            assert nh == self.num_heads and b == B and c * nh == C
        else:
            L = 0

        q = self.query(x).view(B, T, self.num_heads, C // self.num_heads).transpose(1, 2)   # (B, nh, T, hs)
        k = self.key(x).view(B, T, self.num_heads, C // self.num_heads).transpose(1, 2)     # (B, nh, T, hs)
        v = self.value(x).view(B, T, self.num_heads, C // self.num_heads).transpose(1, 2)   # (B, nh, T, hs)

        if kv_cache is not None:
            kv_cache.update(k, v)
            k, v = kv_cache.get()

        att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
        att = att.masked_fill(self.mask[L:L + T, :L + T] == 0, float('-inf'))
        att = F.softmax(att, dim=-1)
        att = self.attn_drop(att)
        y = att @ v
        y = rearrange(y, 'b h t e -> b t (h e)')

        y = self.resid_drop(self.proj(y))

        return y

class WorldModelEnv:

    def __init__(self, tokenizer: torch.nn.Module, world_model: torch.nn.Module, device: Union[str, torch.device], env: Optional[gym.Env] = None) -> None:

        self.device = torch.device(device)
        self.world_model = world_model.to(self.device).eval()
        self.tokenizer = tokenizer.to(self.device).eval()

        self.keys_values_wm, self.obs_tokens, self._num_observations_tokens = None, None, None

        self.env = env

    @property
    def num_observations_tokens(self) -> int:
        return self._num_observations_tokens

    @torch.no_grad()
    def reset(self) -> torch.FloatTensor:
        assert self.env is not None
        obs = torchvision.transforms.functional.to_tensor(self.env.reset()).to(self.device).unsqueeze(0)  # (1, C, H, W) in [0., 1.]
        return self.reset_from_initial_observations(obs)

    @torch.no_grad()
    def reset_from_initial_observations(self, observations: torch.FloatTensor) -> torch.FloatTensor:
        obs_tokens = self.tokenizer.encode(observations, should_preprocess=True).tokens    # (B, C, H, W) -> (B, K)
        _, num_observations_tokens = obs_tokens.shape
        if self.num_observations_tokens is None:
            self._num_observations_tokens = num_observations_tokens

        _ = self.refresh_keys_values_with_initial_obs_tokens(obs_tokens)
        self.obs_tokens = obs_tokens

        return self.decode_obs_tokens()

    @torch.no_grad()
    def refresh_keys_values_with_initial_obs_tokens(self, obs_tokens: torch.LongTensor) -> torch.FloatTensor:
        n, num_observations_tokens = obs_tokens.shape
        assert num_observations_tokens == self.num_observations_tokens
        self.keys_values_wm = self.world_model.transformer.generate_empty_keys_values(n=n, max_tokens=self.world_model.config.max_tokens)
        outputs_wm = self.world_model(obs_tokens, past_keys_values=self.keys_values_wm)
        return outputs_wm.output_sequence  # (B, K, E)

    @torch.no_grad()
    def step(self, action: Union[int, np.ndarray, torch.LongTensor], should_predict_next_obs: bool = True) -> None:
        assert self.keys_values_wm is not None and self.num_observations_tokens is not None

        num_passes = 1 + self.num_observations_tokens if should_predict_next_obs else 1

        output_sequence, obs_tokens = [], []

        if self.keys_values_wm.size + num_passes > self.world_model.config.max_tokens:
            _ = self.refresh_keys_values_with_initial_obs_tokens(self.obs_tokens)

        token = action.clone().detach() if isinstance(action, torch.Tensor) else torch.tensor(action, dtype=torch.long)
        token = token.reshape(-1, 1).to(self.device)  # (B, 1)

        for k in range(num_passes):  # assumption that there is only one action token.

            outputs_wm = self.world_model(token, past_keys_values=self.keys_values_wm)
            output_sequence.append(outputs_wm.output_sequence)

            if k == 0:
                reward = Categorical(logits=outputs_wm.logits_rewards).sample().float().cpu().numpy().reshape(-1) - 1   # (B,)
                done = Categorical(logits=outputs_wm.logits_ends).sample().cpu().numpy().astype(bool).reshape(-1)       # (B,)

            if k < self.num_observations_tokens:
                token = Categorical(logits=outputs_wm.logits_observations).sample()
                obs_tokens.append(token)

        output_sequence = torch.cat(output_sequence, dim=1)   # (B, 1 + K, E)
        self.obs_tokens = torch.cat(obs_tokens, dim=1)        # (B, K)

        obs = self.decode_obs_tokens() if should_predict_next_obs else None
        return obs, reward, done, None

    @torch.no_grad()
    def render_batch(self) -> List[Image.Image]:
        frames = self.decode_obs_tokens().detach().cpu()
        frames = rearrange(frames, 'b c h w -> b h w c').mul(255).numpy().astype(np.uint8)
        return [Image.fromarray(frame) for frame in frames]

    @torch.no_grad()
    def decode_obs_tokens(self) -> List[Image.Image]:
        embedded_tokens = self.tokenizer.embedding(self.obs_tokens)     # (B, K, E)
        z = rearrange(embedded_tokens, 'b (h w) e -> b e h w', h=int(np.sqrt(self.num_observations_tokens)))
        rec = self.tokenizer.decode(z, should_postprocess=True)         # (B, C, H, W)
        return torch.clamp(rec, 0, 1)

    @torch.no_grad()
    def render(self):
        assert self.obs_tokens.shape == (1, self.num_observations_tokens)
        return self.render_batch()[0]




class WorldModelOutput:
    output_sequence: torch.FloatTensor
    logits_observations: torch.FloatTensor
    logits_rewards: torch.FloatTensor
    logits_ends: torch.FloatTensor


class WorldModel(nn.Module):
    def __init__(self, obs_vocab_size: int, act_vocab_size: int, config: TransformerConfig) -> None:
        super().__init__()
        self.obs_vocab_size, self.act_vocab_size = obs_vocab_size, act_vocab_size
        self.config = config
        self.transformer = Transformer(config)

        all_but_last_obs_tokens_pattern = torch.ones(config.tokens_per_block)
        all_but_last_obs_tokens_pattern[-2] = 0
        act_tokens_pattern = torch.zeros(self.config.tokens_per_block)
        act_tokens_pattern[-1] = 1
        obs_tokens_pattern = 1 - act_tokens_pattern

        self.pos_emb = nn.Embedding(config.max_tokens, config.embed_dim)

        self.embedder = Embedder(
            max_blocks=config.max_blocks,
            block_masks=[act_tokens_pattern, obs_tokens_pattern],
            embedding_tables=nn.ModuleList([nn.Embedding(act_vocab_size, config.embed_dim), nn.Embedding(obs_vocab_size, config.embed_dim)])
        )

        self.head_observations = Head(
            max_blocks=config.max_blocks,
            block_mask=all_but_last_obs_tokens_pattern,
            head_module=nn.Sequential(
                nn.Linear(config.embed_dim, config.embed_dim),
                nn.ReLU(),
                nn.Linear(config.embed_dim, obs_vocab_size)
            )
        )

        self.head_rewards = Head(
            max_blocks=config.max_blocks,
            block_mask=act_tokens_pattern,
            head_module=nn.Sequential(
                nn.Linear(config.embed_dim, config.embed_dim),
                nn.ReLU(),
                nn.Linear(config.embed_dim, 3)
            )
        )

        self.head_ends = Head(
            max_blocks=config.max_blocks,
            block_mask=act_tokens_pattern,
            head_module=nn.Sequential(
                nn.Linear(config.embed_dim, config.embed_dim),
                nn.ReLU(),
                nn.Linear(config.embed_dim, 2)
            )
        )

        self.apply(init_weights)

    def __repr__(self) -> str:
        return "world_model"

    def forward(self, tokens: torch.LongTensor, past_keys_values: Optional[KeysValues] = None) -> WorldModelOutput:

        num_steps = tokens.size(1)  # (B, T)
        assert num_steps <= self.config.max_tokens
        prev_steps = 0 if past_keys_values is None else past_keys_values.size

        sequences = self.embedder(tokens, num_steps, prev_steps) + self.pos_emb(prev_steps + torch.arange(num_steps, device=tokens.device))

        x, transformer_hidden_states = self.transformer(sequences, past_keys_values)

        logits_observations, head_hidden_states_observations = self.head_observations(x, num_steps=num_steps, prev_steps=prev_steps)
        logits_rewards, head_hidden_states_rewards = self.head_rewards(x, num_steps=num_steps, prev_steps=prev_steps)
        logits_ends, head_hidden_states_ends = self.head_ends(x, num_steps=num_steps, prev_steps=prev_steps)

        return WorldModelOutput(x, logits_observations, logits_rewards, logits_ends), (transformer_hidden_states, head_hidden_states_observations, head_hidden_states_rewards, head_hidden_states_ends)

    def compute_loss(self, batch: Batch, tokenizer: Tokenizer, **kwargs: Any) -> LossWithIntermediateLosses:

        with torch.no_grad():
            obs_tokens = tokenizer.encode(batch['observations'], should_preprocess=True).tokens  # (BL, K)

        act_tokens = rearrange(batch['actions'], 'b l -> b l 1')
        tokens = rearrange(torch.cat((obs_tokens, act_tokens), dim=2), 'b l k1 -> b (l k1)')  # (B, L(K+1))

        outputs = self(tokens)

        labels_observations, labels_rewards, labels_ends = self.compute_labels_world_model(obs_tokens, batch['rewards'], batch['ends'], batch['mask_padding'])

        logits_observations = rearrange(outputs.logits_observations[:, :-1], 'b t o -> (b t) o')
        loss_obs = F.cross_entropy(logits_observations, labels_observations)
        loss_rewards = F.cross_entropy(rearrange(outputs.logits_rewards, 'b t e -> (b t) e'), labels_rewards)
        loss_ends = F.cross_entropy(rearrange(outputs.logits_ends, 'b t e -> (b t) e'), labels_ends)

        return LossWithIntermediateLosses(loss_obs=loss_obs, loss_rewards=loss_rewards, loss_ends=loss_ends)

    def compute_labels_world_model(self, obs_tokens: torch.Tensor, rewards: torch.Tensor, ends: torch.Tensor, mask_padding: torch.BoolTensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        assert torch.all(ends.sum(dim=1) <= 1)  # at most 1 done
        mask_fill = torch.logical_not(mask_padding)
        labels_observations = rearrange(obs_tokens.masked_fill(mask_fill.unsqueeze(-1).expand_as(obs_tokens), -100), 'b t k -> b (t k)')[:, 1:]
        labels_rewards = (rewards.sign() + 1).masked_fill(mask_fill, -100).long()  # Rewards clipped to {-1, 0, 1}
        labels_ends = ends.masked_fill(mask_fill, -100)
        return labels_observations.reshape(-1), labels_rewards.reshape(-1), labels_ends.reshape(-1)

##########################################################

#acTOR CRITIC

class ActorCritic(nn.Module):
    def __init__(self, act_vocab_size, use_original_obs: bool = False) -> None:
        super().__init__()
        self.use_original_obs = use_original_obs
        self.conv1 = nn.Conv2d(3, 32, 3, stride=1, padding=1)
        self.maxp1 = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 32, 3, stride=1, padding=1)
        self.maxp2 = nn.MaxPool2d(2, 2)
        self.conv3 = nn.Conv2d(32, 64, 3, stride=1, padding=1)
        self.maxp3 = nn.MaxPool2d(2, 2)
        self.conv4 = nn.Conv2d(64, 64, 3, stride=1, padding=1)
        self.maxp4 = nn.MaxPool2d(2, 2)

        self.lstm_dim = 512
        self.lstm = nn.LSTMCell(1024, self.lstm_dim)
        self.hx, self.cx = None, None

        self.critic_linear = nn.Linear(512, 1)
        self.actor_linear = nn.Linear(512, act_vocab_size)

    def __repr__(self) -> str:
        return "actor_critic"

    def clear(self) -> None:
        self.hx, self.cx = None, None

    def reset(self, n: int, burnin_observations: Optional[torch.Tensor] = None, mask_padding: Optional[torch.Tensor] = None) -> None:
        device = self.conv1.weight.device
        self.hx = torch.zeros(n, self.lstm_dim, device=device)
        self.cx = torch.zeros(n, self.lstm_dim, device=device)
        if burnin_observations is not None:
            assert burnin_observations.ndim == 5 and burnin_observations.size(0) == n and mask_padding is not None and burnin_observations.shape[:2] == mask_padding.shape
            for i in range(burnin_observations.size(1)):
                if mask_padding[:, i].any():
                    with torch.no_grad():
                        self(burnin_observations[:, i], mask_padding[:, i])

    def prune(self, mask: np.ndarray) -> None:
        self.hx = self.hx[mask]
        self.cx = self.cx[mask]

    def forward(self, inputs: torch.FloatTensor, mask_padding: Optional[torch.BoolTensor] = None) -> ActorCriticOutput:
        assert inputs.ndim == 4 and inputs.shape[1:] == (3, 64, 64)
        assert 0 <= inputs.min() <= 1 and 0 <= inputs.max() <= 1
        assert mask_padding is None or (mask_padding.ndim == 1 and mask_padding.size(0) == inputs.size(0) and mask_padding.any())
        x = inputs[mask_padding] if mask_padding is not None else inputs

        x = x.mul(2).sub(1)
        hidden_states = ()
        x = F.relu(self.maxp1(self.conv1(x)))
        hidden_states = hidden_states + (x,)
        x = F.relu(self.maxp2(self.conv2(x)))
        hidden_states = hidden_states + (x,)
        x = F.relu(self.maxp3(self.conv3(x)))
        hidden_states = hidden_states + (x,)
        x = F.relu(self.maxp4(self.conv4(x)))
        x = torch.flatten(x, start_dim=1)
        hidden_states = hidden_states + (x,)

        if mask_padding is None:
            self.hx, self.cx = self.lstm(x, (self.hx, self.cx))
        else:
            self.hx[mask_padding], self.cx[mask_padding] = self.lstm(x, (self.hx[mask_padding], self.cx[mask_padding]))
        
        hidden_states = hidden_states + (self.hx,)

        logits_actions = rearrange(self.actor_linear(self.hx), 'b a -> b 1 a')
        means_values = rearrange(self.critic_linear(self.hx), 'b 1 -> b 1 1')

        return ActorCriticOutput(logits_actions, means_values), hidden_states

    def compute_loss(self, batch: Batch, tokenizer: Tokenizer, world_model: WorldModel, imagine_horizon: int, gamma: float, lambda_: float, entropy_weight: float, **kwargs: Any) -> LossWithIntermediateLosses:
        assert not self.use_original_obs
        outputs = self.imagine(batch, tokenizer, world_model, horizon=imagine_horizon)

        with torch.no_grad():
            lambda_returns = compute_lambda_returns(
                rewards=outputs.rewards,
                values=outputs.values,
                ends=outputs.ends,
                gamma=gamma,
                lambda_=lambda_,
            )[:, :-1]

        values = outputs.values[:, :-1]

        d = Categorical(logits=outputs.logits_actions[:, :-1])
        log_probs = d.log_prob(outputs.actions[:, :-1])
        loss_actions = -1 * (log_probs * (lambda_returns - values.detach())).mean()
        loss_entropy = - entropy_weight * d.entropy().mean()
        loss_values = F.mse_loss(values, lambda_returns)

        return LossWithIntermediateLosses(loss_actions=loss_actions, loss_values=loss_values, loss_entropy=loss_entropy)

    def imagine(self, batch: Batch, tokenizer: Tokenizer, world_model: WorldModel, horizon: int, show_pbar: bool = False) -> ImagineOutput:
        assert not self.use_original_obs
        initial_observations = batch['observations']
        mask_padding = batch['mask_padding']
        assert initial_observations.ndim == 5 and initial_observations.shape[2:] == (3, 64, 64)
        assert mask_padding[:, -1].all()
        device = initial_observations.device
        wm_env = WorldModelEnv(tokenizer, world_model, device)

        all_actions = []
        all_logits_actions = []
        all_values = []
        all_rewards = []
        all_ends = []
        all_observations = []

        burnin_observations = torch.clamp(tokenizer.encode_decode(initial_observations[:, :-1], should_preprocess=True, should_postprocess=True), 0, 1) if initial_observations.size(1) > 1 else None
        self.reset(n=initial_observations.size(0), burnin_observations=burnin_observations, mask_padding=mask_padding[:, :-1])

        obs = wm_env.reset_from_initial_observations(initial_observations[:, -1])
        for k in tqdm(range(horizon), disable=not show_pbar, desc='Imagination', file=sys.stdout):

            all_observations.append(obs)

            outputs_ac = self(obs)
            action_token = Categorical(logits=outputs_ac.logits_actions).sample()
            obs, reward, done, _ = wm_env.step(action_token, should_predict_next_obs=(k < horizon - 1))

            all_actions.append(action_token)
            all_logits_actions.append(outputs_ac.logits_actions)
            all_values.append(outputs_ac.means_values)
            all_rewards.append(torch.tensor(reward).reshape(-1, 1))
            all_ends.append(torch.tensor(done).reshape(-1, 1))

        self.clear()

        return ImagineOutput(
            observations=torch.stack(all_observations, dim=1).mul(255).byte(),      # (B, T, C, H, W) in [0, 255]
            actions=torch.cat(all_actions, dim=1),                                  # (B, T)
            logits_actions=torch.cat(all_logits_actions, dim=1),                    # (B, T, #actions)
            values=rearrange(torch.cat(all_values, dim=1), 'b t 1 -> b t'),         # (B, T)
            rewards=torch.cat(all_rewards, dim=1).to(device),                       # (B, T)
            ends=torch.cat(all_ends, dim=1).to(device),                             # (B, T)
        )

######################################################################
#AGENT
class Agent(nn.Module):
    def __init__(self, tokenizer: Tokenizer, world_model: WorldModel, actor_critic: ActorCritic):
        super().__init__()
        self.tokenizer = tokenizer
        self.world_model = world_model
        self.actor_critic = actor_critic

    @property
    def device(self):
        return self.actor_critic.conv1.weight.device

    def load(self, path_to_checkpoint: Path, device: torch.device, load_tokenizer: bool = True, load_world_model: bool = True, load_actor_critic: bool = True) -> None:
        agent_state_dict = torch.load(path_to_checkpoint, map_location=device)
        if load_tokenizer:
            self.tokenizer.load_state_dict(extract_state_dict(agent_state_dict, 'tokenizer'))
        if load_world_model:
            self.world_model.load_state_dict(extract_state_dict(agent_state_dict, 'world_model'))
        if load_actor_critic:
            self.actor_critic.load_state_dict(extract_state_dict(agent_state_dict, 'actor_critic'))

    def act(self, obs: torch.FloatTensor, should_sample: bool = True, temperature: float = 1.0) -> torch.LongTensor:
        input_ac = obs if self.actor_critic.use_original_obs else torch.clamp(self.tokenizer.encode_decode(obs, should_preprocess=True, should_postprocess=True), 0, 1)
        logits_actions = self.actor_critic(input_ac).logits_actions[:, -1] / temperature
        act_token = Categorical(logits=logits_actions).sample() if should_sample else logits_actions.argmax(dim=-1)
        return act_token

#########################################################################################################################

###########################################################################################################





################################################################################################
@add_start_docstrings("The IRIS Model", IRIS_START_DOCSTRING)
# Copied from transformers.models.decision_transformer.modeling_decision_transformer.DecisionTransformerModel with DecisionTransformer->Iris,edbeeching/decision-transformer-gym-hopper-medium->ruffy369/iris-breakout
class IrisModel(IrisPreTrainedModel):
    """

    The model builds upon the GPT2 architecture to perform autoregressive prediction of actions in an offline RL
    setting. Refer to the paper for more details: https://arxiv.org/abs/2106.01345

    """

    #MAKE SURE TO SUPPORT OUTPUT HIDDEN STATES AND OUTPUT ATTENTIONS###################
    
    def __init__(self, config):
        super().__init__(config)
        
        self.cfg = config
        self.start_epoch = 1
        self.device = torch.device(self.cfg.common.device)

        self.ckpt_dir = Path('checkpoints')
        self.media_dir = Path('media')
        self.episode_dir = self.media_dir / 'episodes'
        self.reconstructions_dir = self.media_dir / 'reconstructions'

        if not self.cfg.common.resume:
            config_dir = Path('config')
            config_path = config_dir / 'trainer.yaml'
            config_dir.mkdir(exist_ok=False, parents=False)
            shutil.copy('.hydra/config.yaml', config_path)
            shutil.copytree(src=(Path(hydra.utils.get_original_cwd()) / "src"), dst="./src")
            shutil.copytree(src=(Path(hydra.utils.get_original_cwd()) / "scripts"), dst="./scripts")
            self.ckpt_dir.mkdir(exist_ok=False, parents=False)
            self.media_dir.mkdir(exist_ok=False, parents=False)
            self.episode_dir.mkdir(exist_ok=False, parents=False)
            self.reconstructions_dir.mkdir(exist_ok=False, parents=False)

        episode_manager_train = EpisodeDirManager(self.episode_dir / 'train', max_num_episodes=self.cfg.collection.train.num_episodes_to_save)
        episode_manager_test = EpisodeDirManager(self.episode_dir / 'test', max_num_episodes=self.cfg.collection.test.num_episodes_to_save)
        self.episode_manager_imagination = EpisodeDirManager(self.episode_dir / 'imagination', max_num_episodes=self.cfg.evaluation.actor_critic.num_episodes_to_save)

        def create_env(cfg_env, num_envs):
            env_fn = partial(instantiate, config=cfg_env)
            return MultiProcessEnv(env_fn, num_envs, should_wait_num_envs_ratio=1.0) if num_envs > 1 else SingleProcessEnv(env_fn)

        if self.cfg.training.should:
            train_env = create_env(self.cfg.env.train, self.cfg.collection.train.num_envs)
            self.train_dataset = instantiate(self.cfg.datasets.train)
            self.train_collector = Collector(train_env, self.train_dataset, episode_manager_train)

        if self.cfg.evaluation.should:
            test_env = create_env(self.cfg.env.test, self.cfg.collection.test.num_envs)
            self.test_dataset = instantiate(cfg.datasets.test)
            self.test_collector = Collector(test_env, self.test_dataset, episode_manager_test)

        assert self.cfg.training.should or self.cfg.evaluation.should
        env = train_env if self.cfg.training.should else test_env

        tokenizer = instantiate(self.cfg.tokenizer)
        world_model = WorldModel(obs_vocab_size=tokenizer.vocab_size, act_vocab_size=env.num_actions, config=instantiate(self.cfg.world_model))
        actor_critic = ActorCritic(**self.cfg.actor_critic, act_vocab_size=env.num_actions)
        self.agent = Agent(tokenizer, world_model, actor_critic).to(self.device)
        print(f'{sum(p.numel() for p in self.agent.tokenizer.parameters())} parameters in agent.tokenizer')
        print(f'{sum(p.numel() for p in self.agent.world_model.parameters())} parameters in agent.world_model')
        print(f'{sum(p.numel() for p in self.agent.actor_critic.parameters())} parameters in agent.actor_critic')

        self.optimizer_tokenizer = torch.optim.Adam(self.agent.tokenizer.parameters(), lr=self.cfg.training.learning_rate)
        self.optimizer_world_model = configure_optimizer(self.agent.world_model, self.cfg.training.learning_rate, self.cfg.training.world_model.weight_decay)
        self.optimizer_actor_critic = torch.optim.Adam(self.agent.actor_critic.parameters(), lr=self.cfg.training.learning_rate)

        if self.cfg.initialization.path_to_checkpoint is not None:
            self.agent.load(**self.cfg.initialization, device=self.device)

        if self.cfg.common.resume:
            self.load_checkpoint()

        # Initialize weights and apply final processing
        self.post_init()


    def forward_component(self, component: nn.Module, **kwargs):
        output1, output2, output3, all_hidden_states = component.forward(**kwargs)
        return (output1, output2, output3), all_hidden_states
    
    def component_losses(self, component: nn.Module, batch, grad_acc_steps: int, **kwargs_loss:Any):
        losses = component.compute_loss(batch, **kwargs_loss) / grad_acc_steps
        losses = losses.loss_total
        return losses
        
    @add_start_docstrings_to_model_forward(IRIS_INPUTS_DOCSTRING)
    @replace_return_docstrings(output_type=IrisOutput, config_class=_CONFIG_FOR_DOC)
    def forward(
        self,
        observations: Optional[torch.FloatTensor] = None,
        actions: Optional[torch.FloatTensor] = None,
        rewards: Optional[torch.FloatTensor] = None,
        ends: Optional[torch.IntTensor] = None,
        mask_padding: Optional[torch.BoolTensor] = None,
        should_preprocess: Optional[bool] = None,
        should_postprocess: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        return_dict: Optional[bool] = None,
    ) -> Union[Tuple[torch.FloatTensor], IrisOutput]:
        r"""
        Returns:

        Examples:

        ```python
        >>> from transformers import IrisModel
        >>> import torch

        >>> model = IrisModel.from_pretrained("ruffy369/iris-breakout")
        >>> # evaluation
        >>> model = model.to(device)
        >>> model.eval()

        >>> env = create_env(self.cfg.env.train, self.cfg.collection.train.num_envs)
        >>> state_dim = env.observation_space.shape[0]
        >>> act_dim = env.action_space.shape[0]

        >>> state = env.reset()
        >>> states = torch.from_numpy(state).reshape(1, 1, state_dim).to(device=device, dtype=torch.float32)
        >>> actions = torch.zeros((1, 1, act_dim), device=device, dtype=torch.float32)
        >>> rewards = torch.zeros(1, 1, device=device, dtype=torch.float32)
        >>> target_return = torch.tensor(TARGET_RETURN, dtype=torch.float32).reshape(1, 1)
        >>> timesteps = torch.tensor(0, device=device, dtype=torch.long).reshape(1, 1)
        >>> attention_mask = torch.zeros(1, 1, device=device, dtype=torch.float32)

        >>> # forward pass
        >>> with torch.no_grad():
        ...     state_preds, action_preds, return_preds = model(
        ...         observations = observations,
                    should_preprocess = True,
                    should_postprocess = True,
                    output_hidden_states = False,
                    output_attentions = False,
                    return_dict = True,
        ...     )
        ```"""

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )


        cfg_tokenizer = self.cfg.training.tokenizer
        cfg_world_model = self.cfg.training.world_model
        cfg_actor_critic = self.cfg.training.actor_critic

        batch = dict(observations = observations, actions = actions, rewards = rewards, ends = ends, mask_padding = mask_padding)
        batch = batch.to(self.device)
               
        losses_tokenizer = self.component_losses(self.agent.tokenizer, batch, **cfg_tokenizer)
        losses_world_model = self.component_losses(self.agent.world_model, batch, **cfg_world_model)
        losses_actor_critic = self.component_losses(self.agent.actor_critic, batch, **cfg_actor_critic)
        losses = dict(tokenizer_losses = losses_tokenizer, world_model_losses = losses_world_model, actor_critic_losses = losses_actor_critic)

        if should_preprocess == True:
            # preprocess observations
            observations_for_tokenizer = self.agent.tokenizer.preprocess_input(observations)
        #tokenizer outputs = (outputs.z, outputs.z_quantized, reconstructions)
        tokenizer_outputs,all_hidden_states_tokenizer = self.forward_component(self.agent.tokenizer, x=observations_for_tokenizer, should_preprocess= should_preprocess, should_postprocess= should_postprocess)

        with torch.no_grad():
            obs_tokens = self.agent.tokenizer.encode(observations, should_preprocess=should_preprocess).tokens
        act_tokens = rearrange(self.agent.act(observations, should_sample=self.cfg.should_sample, temperature=self.cfg.temperature), 'b l -> b l 1')
        tokens = rearrange(torch.cat((obs_tokens, act_tokens), dim=2), 'b l k1 -> b (l k1)')  # (B, L(K+1))
        #world_model_outputs = WorldModelOutput() instance
        world_model_outputs, all_hidden_states_world_model = self.forward_component(self.agent.world_model, tokens = tokens)[0]

        wm_env = WorldModelEnv(self.agent.tokenizer, self.agent.world_model, self.cfg.common.device)
        obs = wm_env.reset_from_initial_observations(observations[:, -1])
        #actor_critic_outputs = ActorCriticOutput() instance
        actor_critic_outputs, all_hidden_states_actor_critic = self.forward_component(self.agent.actor_critic, inputs = obs)[0]

        all_hidden_states = (all_hidden_states_tokenizer, all_hidden_states_world_model, all_hidden_states_actor_critic) if output_hidden_states else None
            
       
        return IrisOutput(
            losses = losses,
            reconstructed_img = tokenizer_outputs[2],
            action_preds = actor_critic_outputs.actions,
            reward_preds = actor_critic_outputs.rewards,
            epsiode_end = actor_critic_outputs.ends,
            obs_preds = actor_critic_outputs.observations,
            hidden_states = all_hidden_states, 
            attentions = None,
        )