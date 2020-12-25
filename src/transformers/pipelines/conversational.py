import uuid
from typing import List, Optional, Union

from ..file_utils import add_end_docstrings, is_tf_available, is_torch_available
from ..utils import logging
from .base import PIPELINE_INIT_ARGS, Pipeline


if is_tf_available():
    import tensorflow as tf

if is_torch_available():
    import torch


logger = logging.get_logger(__name__)


class Conversation:
    """
    Utility class containing a conversation and its history. This class is meant to be used as an input to the
    :class:`~transformers.ConversationalPipeline`. The conversation contains a number of utility function to manage the
    addition of new user input and generated model responses. A conversation needs to contain an unprocessed user input
    before being passed to the :class:`~transformers.ConversationalPipeline`. This user input is either created when
    the class is instantiated, or by calling :obj:`conversational_pipeline.append_response("input")` after a
    conversation turn.

    Arguments:
        text (:obj:`str`, `optional`):
            The initial user input to start the conversation. If not provided, a user input needs to be provided
            manually using the :meth:`~transformers.Conversation.add_user_input` method before the conversation can
            begin.
        conversation_id (:obj:`uuid.UUID`, `optional`):
            Unique identifier for the conversation. If not provided, a random UUID4 id will be assigned to the
            conversation.

    Usage::

        conversation = Conversation("Going to the movies tonight - any suggestions?")

        # Steps usually performed by the model when generating a response:
        # 1. Mark the user input as processed (moved to the history)
        conversation.mark_processed()
        # 2. Append a mode response
        conversation.append_response("The Big lebowski.")

        conversation.add_user_input("Is it good?")
    """

    def __init__(
        self, text: str = None, conversation_id: uuid.UUID = None, past_user_inputs=None, generated_responses=None
    ):
        if not conversation_id:
            conversation_id = uuid.uuid4()
        self.uuid: uuid.UUID = conversation_id
        if past_user_inputs is None:
            past_user_inputs = past_user_inputs
        self.past_user_inputs: List[str] = []
        if generated_responses is None:
            generated_responses = []
        self.generated_responses: List[str] = generated_responses
        self.history: List[int] = []
        self.new_user_input: Optional[str] = text

    def add_user_input(self, text: str, overwrite: bool = False):
        """
        Add a user input to the conversation for the next round. This populates the internal :obj:`new_user_input`
        field.

        Args:
            text (:obj:`str`): The user input for the next conversation round.
            overwrite (:obj:`bool`, `optional`, defaults to :obj:`False`):
                Whether or not existing and unprocessed user input should be overwritten when this function is called.
        """
        if self.new_user_input:
            if overwrite:
                logger.warning(
                    'User input added while unprocessed input was existing: "{}" was overwritten with: "{}".'.format(
                        self.new_user_input, text
                    )
                )
                self.new_user_input = text
            else:
                logger.warning(
                    'User input added while unprocessed input was existing: "{}" new input ignored: "{}". '
                    "Set `overwrite` to True to overwrite unprocessed user input".format(self.new_user_input, text)
                )
        else:
            self.new_user_input = text

    def mark_processed(self):
        """
        Mark the conversation as processed (moves the content of :obj:`new_user_input` to :obj:`past_user_inputs`) and
        empties the :obj:`new_user_input` field.
        """
        if self.new_user_input:
            self.past_user_inputs.append(self.new_user_input)
        self.new_user_input = None

    def append_response(self, response: str):
        """
        Append a response to the list of generated responses.

        Args:
            response (:obj:`str`): The model generated response.
        """
        self.generated_responses.append(response)

    def set_history(self, history: List[int]):
        """
        Updates the value of the history of the conversation. The history is represented by a list of :obj:`token_ids`.
        The history is used by the model to generate responses based on the previous conversation turns.

        Args:
            history (:obj:`List[int]`): History of tokens provided and generated for this conversation.
        """
        self.history = history

    def __repr__(self):
        """
        Generates a string representation of the conversation.

        Return:
            :obj:`str`:

            Example: Conversation id: 7d15686b-dc94-49f2-9c4b-c9eac6a1f114 user >> Going to the movies tonight - any
            suggestions? bot >> The Big Lebowski
        """
        output = "Conversation id: {} \n".format(self.uuid)
        for user_input, generated_response in zip(self.past_user_inputs, self.generated_responses):
            output += "user >> {} \n".format(user_input)
            output += "bot >> {} \n".format(generated_response)
        if self.new_user_input is not None:
            output += "user >> {} \n".format(self.new_user_input)
        return output


@add_end_docstrings(
    PIPELINE_INIT_ARGS,
    r"""
        min_length_for_response (:obj:`int`, `optional`, defaults to 32):
            The minimum length (in number of tokens) for a response.
    """,
)
class ConversationalPipeline(Pipeline):
    """
    Multi-turn conversational pipeline.

    This conversational pipeline can currently be loaded from :func:`~transformers.pipeline` using the following task
    identifier: :obj:`"conversational"`.

    The models that this pipeline can use are models that have been fine-tuned on a multi-turn conversational task,
    currently: `'microsoft/DialoGPT-small'`, `'microsoft/DialoGPT-medium'`, `'microsoft/DialoGPT-large'`. See the
    up-to-date list of available models on `huggingface.co/models
    <https://huggingface.co/models?filter=conversational>`__.

    Usage::

        conversational_pipeline = pipeline("conversational")

        conversation_1 = Conversation("Going to the movies tonight - any suggestions?")
        conversation_2 = Conversation("What's the last book you have read?")

        conversational_pipeline([conversation_1, conversation_2])

        conversation_1.add_user_input("Is it an action movie?")
        conversation_2.add_user_input("What is the genre of this book?")

        conversational_pipeline([conversation_1, conversation_2])
    """

    def __init__(self, min_length_for_response=32, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # We need at least an eos_token
        assert self.tokenizer.eos_token_id is not None, "DialoguePipeline tokenizer should have an EOS token set"
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.min_length_for_response = min_length_for_response

    def __call__(
        self,
        conversations: Union[Conversation, List[Conversation]],
        clean_up_tokenization_spaces=True,
        **generate_kwargs
    ):
        r"""
        Generate responses for the conversation(s) given as inputs.

        Args:
            conversations (a :class:`~transformers.Conversation` or a list of :class:`~transformers.Conversation`):
                Conversations to generate responses for.
            clean_up_tokenization_spaces (:obj:`bool`, `optional`, defaults to :obj:`False`):
                Whether or not to clean up the potential extra spaces in the text output.
            generate_kwargs:
                Additional keyword arguments to pass along to the generate method of the model (see the generate method
                corresponding to your framework `here <./model.html#generative-models>`__).

        Returns:
            :class:`~transformers.Conversation` or a list of :class:`~transformers.Conversation`: Conversation(s) with
            updated generated responses for those containing a new user input.
        """

        if isinstance(conversations, Conversation):
            conversations = [conversations]
        # Input validation
        if isinstance(conversations, list):
            for conversation in conversations:
                assert isinstance(
                    conversation, Conversation
                ), "DialoguePipeline expects a Conversation or list of Conversations as an input"
                if conversation.new_user_input is None:
                    raise ValueError(
                        "Conversation with UUID {} does not contain new user input to process. "
                        "Add user inputs with the conversation's `add_user_input` method".format(
                            type(conversation.uuid)
                        )
                    )
            assert (
                self.tokenizer.pad_token_id is not None or self.tokenizer.eos_token_id is not None
            ), "Please make sure that the tokenizer has a pad_token_id or eos_token_id when using a batch input"
        else:
            raise ValueError("DialoguePipeline expects a Conversation or list of Conversations as an input")

        with self.device_placement():

            inputs = self._parse_and_tokenize([conversation.new_user_input for conversation in conversations])
            histories = [conversation.history for conversation in conversations]
            max_length = generate_kwargs.get("max_length", self.model.config.max_length)
            inputs = self._concat_inputs_history(inputs, histories, max_length)

            if self.framework == "pt":
                inputs = self.ensure_tensor_on_device(**inputs)
                input_length = inputs["input_ids"].shape[-1]

            elif self.framework == "tf":
                input_length = tf.shape(inputs["input_ids"])[-1].numpy()

            if input_length > 0.9 * max_length:
                logger.warning(
                    "Longest conversation length: {} is bigger than 0.9 * max_length: {}. "
                    "You might consider trimming the early phase of the conversation".format(input_length, max_length)
                )
            generated_responses = self.model.generate(
                inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                **generate_kwargs,
            )

            if self.model.config.is_encoder_decoder:
                if self.framework == "pt":
                    history = torch.cat((inputs["input_ids"], generated_responses[:, 1:]), 1)
                elif self.framework == "tf":
                    history = tf.concat([inputs["input_ids"], generated_responses[:, 1:]], 1)
            else:
                history = generated_responses

            history = self._clean_padding_history(history)
            if self.model.config.is_encoder_decoder:
                start_position = 1
            else:
                start_position = input_length

            output = []
            for conversation_index, conversation in enumerate(conversations):
                conversation.mark_processed()
                conversation.generated_responses.append(
                    self.tokenizer.decode(
                        generated_responses[conversation_index][start_position:],
                        skip_special_tokens=True,
                        clean_up_tokenization_spaces=clean_up_tokenization_spaces,
                    )
                )
                conversation.set_history(history[conversation_index])
                output.append(conversation)
            if len(output) == 1:
                return output[0]
            else:
                return output

    def _parse_and_tokenize(self, inputs, **kwargs):
        """
        Parse arguments and tokenize, adding an EOS token at the end of the user input
        """
        # Parse arguments
        inputs = self.tokenizer(inputs, add_special_tokens=False, padding=False).get("input_ids", [])
        for input in inputs:
            input.append(self.tokenizer.eos_token_id)
        return inputs

    def _clean_padding_history(self, generated_tensor) -> List[List[int]]:
        """
        Cleans the padding history. Padding may be generated in two places when multiple conversations are provided as
        an input:

            - at the end of the concatenated history and new user input, so that all input to the model have the same
              length
            - at the end of the generated response, as some responses will be longer than others
        This method cleans up these padding token so that the history for each conversation is not impacted by the
        batching process.
        """
        outputs = []
        for sequence in generated_tensor:
            sequence_tokens = []
            is_previous_pad = False
            for token in sequence:
                if token == self.tokenizer.pad_token_id:
                    if self.tokenizer.pad_token_id != self.tokenizer.eos_token_id:
                        continue
                    if is_previous_pad:
                        continue
                    else:
                        is_previous_pad = True
                else:
                    is_previous_pad = False
                if self.framework == "pt":
                    sequence_tokens.append(token.item())
                else:
                    sequence_tokens.append(int(token.numpy()))

            outputs.append(sequence_tokens)
        return outputs

    def _concat_inputs_history(self, inputs: List[List[int]], histories: List[Optional[List[int]]], max_length: int):
        """
        Builds an input prepended by the history for this conversation, allowing multi-turn conversation with context
        """
        outputs = []
        for new_input, history in zip(inputs, histories):
            if history is not None:
                new_input = history + new_input
            if len(new_input) > max_length - self.min_length_for_response:
                cutoff_eos_index = 0
                while len(new_input) - cutoff_eos_index > max_length - self.min_length_for_response:
                    if cutoff_eos_index >= len(new_input):
                        break
                    cutoff_eos_index = new_input[cutoff_eos_index:].index(self.tokenizer.eos_token_id)
                    if cutoff_eos_index == 0 or cutoff_eos_index == len(new_input) - 1:
                        break
                    else:
                        new_input = new_input[cutoff_eos_index + 1 :]
            outputs.append(new_input)
        padded_outputs = self.tokenizer.pad(
            {"input_ids": outputs}, padding="longest", return_attention_mask=True, return_tensors=self.framework
        )
        return padded_outputs
