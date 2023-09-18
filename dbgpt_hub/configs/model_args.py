import os
import yaml
from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Dict, List,Literal
from transformers import Seq2SeqTrainingArguments
from dbgpt_hub.configs.config import (
    MODEL_PATH,
    DEFAULT_FT_MODEL_NAME,
    DATA_PATH,
    ADAPTER_PATH,
)

# Config this from config.py
model_path = os.path.join(MODEL_PATH, DEFAULT_FT_MODEL_NAME)


@dataclass
class ModelArguments:
    model_name_or_path: Optional[str] = field(
        default=model_path,
        metadata={
            "help": (
                "The model checkpoint for weights initialization. Don't set if you want to\
              train a model from scratch."
            )
        },
    )
    tokenizer_name: Optional[str] = field(
        default=None,
        metadata={
            "help": "Pretrained tokenizer name or path if not the same as model_name"
        },
    )
    model_revision: str = field(
        default="main",
        metadata={
            "help": "The specific model version to use (can be a branch name, tag name or commit id)."
        },
    )
    trust_remote_code: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Enable unpickling of arbitrary code in AutoModelForCausalLM#from_pretrained."
        },
    )
    use_auth_token: Optional[bool] = field(
        default=False,
        metadata={"help": "Enables using Huggingface auth token from Git Credentials."},
    )


@dataclass
class ModelInferenceArguments:
    cache_dir: Optional[str] = field(default=None)
    model_name_or_path: Optional[str] = field(
        default=model_path, metadata={"help": "Path to pre-trained model"}
    )
    model_max_length: int = field(
        default=1024,
        metadata={
            "help": "Maximum sequence length. Sequences will be right padded (and possibly truncated)."
        },
    )
    prompt_template: str = field(
        default="default",
        metadata={
            "help": "Prompt template name. Such as vanilla, alpaca, llama2, vicuna..., etc."
        },
    )
    source_prefix: Optional[str] = field(
        default=None, metadata={"help": "Prefix to prepend to every source text."}
    )


@dataclass
class DatasetAttr(object):
    dataset_name: Optional[str] = None
    hf_hub_url: Optional[str] = None
    local_path: Optional[str] = None
    dataset_format: Optional[str] = None
    dataset_sha1: Optional[str] = None
    load_from_local: bool = False
    multi_turn: Optional[bool] = False

    def __repr__(self) -> str:
        rep = (
            f"dataset_name: {self.dataset_name} || "
            f"hf_hub_url: {self.hf_hub_url} || "
            f"local_path: {self.local_path} \n"
            f"data_formate: {self.dataset_format}  || "
            f"load_from_local: {self.load_from_local} || "
            f"multi_turn: {self.multi_turn}"
        )
        return rep

    def __post_init__(self):
        self.prompt_column = "instruction"
        self.query_column = "input"
        self.response_column = "output"
        self.history_column = None


@dataclass
class DataArguments:
    dataset_name: Optional[str] = field(
        default="spider",
        metadata={"help": "Which dataset to finetune on. See datamodule for options."},
    )

    dataset_dir: str = field(
        default=None,
        metadata={"help": "where is dataset in local dir. See datamodule for options."},
    )
    instruction_template: str = field(
        default="default",
        metadata={
            "help": "Which template to use for constructing prompts in training and inference."
        },
    )
    conversation_template: str = field(
        default="default",
        metadata={
            "help": "Which template to use for constructing prompts in multi-turn dataset training and inference."
        },
    )
    eval_dataset_size: Optional[float] = field(
        default=0.1, metadata={"help": "Size of validation dataset."}
    )

    max_train_samples: Optional[int] = field(
        default=None,
        metadata={
            "help": "For debugging purposes or quicker training, truncate the number of training examples to this "
            "value if set."
        },
    )
    source_max_len: int = field(
        default=1024,
        metadata={
            "help": "Maximum source sequence length. Sequences will be right padded (and possibly truncated)."
        },
    )
    target_max_len: int = field(
        default=256,
        metadata={
            "help": "Maximum target sequence length. Sequences will be right padded (and possibly truncated)."
        },
    )
    dataset: str = field(
        default="spider",
        metadata={"help": "Which dataset to finetune on. See datamodule for options."},
    )
    dataset_format: Optional[str] = field(
        default="spider",
        metadata={
            "help": "Which dataset format is used. [alpaca|chip2|self-instruct|hh-rlhf]"
        },
    )

    max_eval_samples: Optional[int] = field(
        default=None,
        metadata={
            "help": "For debugging purposes or quicker training, truncate the number of evaluation examples to this "
            "value if set."
        },
    )

    def init_for_training(self):  # support mixing multiple datasets
        dataset_names = [ds.strip() for ds in self.dataset_name.split(",")]
        datasets_info_path = os.path.join(DATA_PATH, "data_info.yaml")
        with open(datasets_info_path, "r") as f:
            datasets_info = yaml.safe_load(f)

        self.datasets_list: List[DatasetAttr] = []
        for i, name in enumerate(dataset_names):
            if name not in datasets_info:
                raise ValueError(
                    "Undefined dataset {} in {}".format(name, datasets_info_path)
                )

            dataset_attr = DatasetAttr()
            dataset_attr.dataset_name = name
            dataset_attr.dataset_format = datasets_info[name].get(
                "dataset_format", None
            )
            dataset_attr.hf_hub_url = datasets_info[name].get("hf_hub_url", None)
            dataset_attr.local_path = datasets_info[name].get("local_path", None)
            dataset_attr.multi_turn = datasets_info[name].get("multi_turn", False)

            print(datasets_info[name]["local_path"])
            print(os.path.exists(datasets_info[name]["local_path"]))
            print(">>>>>>>>")

            if datasets_info[name]["local_path"] and os.path.exists(
                datasets_info[name]["local_path"]
            ):
                dataset_attr.load_from_local = True
            else:
                dataset_attr.load_from_local = False
                raise Warning(
                    "You have set local_path for {} but it does not exist! Will load the data from {}".format(
                        name, dataset_attr.hf_hub_url
                    )
                )

            if "columns" in datasets_info[name]:
                dataset_attr.prompt_column = datasets_info[name]["columns"].get(
                    "prompt", None
                )
                dataset_attr.query_column = datasets_info[name]["columns"].get(
                    "query", None
                )
                dataset_attr.response_column = datasets_info[name]["columns"].get(
                    "response", None
                )
                dataset_attr.history_column = datasets_info[name]["columns"].get(
                    "history", None
                )

            self.datasets_list.append(dataset_attr)


@dataclass
class GenerationArguments:
    # For more hyperparameters check:
    # https://huggingface.co/docs/transformers/main_classes/text_generation#transformers.GenerationConfig
    # Length arguments
    max_new_tokens: Optional[int] = field(
        default=128,
        metadata={
            "help": "Maximum number of new tokens to be generated in evaluation or prediction loops"
            "if predict_with_generate is set."
        },
    )
    min_new_tokens: Optional[int] = field(
        default=None, metadata={"help": "Minimum number of new tokens to generate."}
    )

    # Generation strategy
    do_sample: Optional[bool] = field(default=False)
    num_beams: Optional[int] = field(default=1)
    num_beam_groups: Optional[int] = field(default=1)
    penalty_alpha: Optional[float] = field(default=None)
    use_cache: Optional[bool] = field(default=False)

    # Hyperparameters for logit manipulation
    temperature: Optional[float] = field(default=1.0)
    top_k: Optional[int] = field(default=50)
    top_p: Optional[float] = field(default=1.0)
    typical_p: Optional[float] = field(default=1.0)
    diversity_penalty: Optional[float] = field(default=0.0)
    repetition_penalty: Optional[float] = field(default=1.0)
    length_penalty: Optional[float] = field(default=1.0)
    no_repeat_ngram_size: Optional[int] = field(default=0)

    def to_dict(self) -> Dict[str, Any]:
        args = asdict(self)
        if args.get("max_new_tokens", None):
            args.pop("max_length", None)
        return args


@dataclass
class FinetuningArguments:
    r"""
    Arguments pertaining to which techniques we are going to fine-tuning with.
    """
    finetuning_type: Optional[Literal["lora", "freeze", "full", "none"]] = field(
        default="lora", metadata={"help": "Which fine-tuning method to use."}
    )
    num_hidden_layers: Optional[int] = field(
        default=32,
        metadata={
            "help": 'Number of decoder blocks in the model for partial-parameter (freeze) fine-tuning. \
                  LLaMA choices: ["32", "40", "60", "80"], \
                  LLaMA-2 choices: ["32", "40", "80"], \
                  BLOOM choices: ["24", "30", "70"], \
                  Falcon choices: ["32", "60"], \
                  Baichuan choices: ["32", "40"] \
                  Qwen choices: ["32"], \
                  XVERSE choices: ["40"], \
                  ChatGLM2 choices: ["28"]'
        },
    )
    num_layer_trainable: Optional[int] = field(
        default=3,
        metadata={
            "help": "Number of trainable layers for partial-parameter (freeze) fine-tuning."
        },
    )
    name_module_trainable: Optional[
        Literal["mlp", "self_attn", "self_attention"]
    ] = field(
        default="mlp",
        metadata={
            "help": 'Name of trainable modules for partial-parameter (freeze) fine-tuning. \
                  LLaMA choices: ["mlp", "self_attn"], \
                  BLOOM & Falcon & ChatGLM2 choices: ["mlp", "self_attention"], \
                  Baichuan choices: ["mlp", "self_attn"], \
                  Qwen choices: ["mlp", "attn"], \
                  LLaMA-2, InternLM, XVERSE choices: the same as LLaMA.'
        },
    )
    lora_rank: Optional[int] = field(
        default=8, metadata={"help": "The intrinsic dimension for LoRA fine-tuning."}
    )
    lora_alpha: Optional[float] = field(
        default=32.0,
        metadata={
            "help": "The scale factor for LoRA fine-tuning (similar with the learning rate)."
        },
    )
    lora_dropout: Optional[float] = field(
        default=0.1, metadata={"help": "Dropout rate for the LoRA fine-tuning."}
    )
    lora_target: Optional[str] = field(
        default=None,
        metadata={
            "help": 'Name(s) of target modules to apply LoRA. Use commas to separate multiple modules. \
                  LLaMA choices: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"], \
                  BLOOM & Falcon & ChatGLM2 choices: ["query_key_value", "self_attention.dense", "mlp.dense"], \
                  Baichuan choices: ["W_pack", "o_proj", "gate_proj", "up_proj", "down_proj"], \
                  Qwen choices: ["c_attn", "attn.c_proj", "w1", "w2", "mlp.c_proj"], \
                  LLaMA-2, InternLM, XVERSE choices: the same as LLaMA.'
        },
    )
    resume_lora_training: Optional[bool] = field(
        default=True,
        metadata={
            "help": "Whether to resume training from the last LoRA weights or create new weights after merging them."
        },
    )
    ppo_score_norm: Optional[bool] = field(
        default=False, metadata={"help": "Use score normalization in PPO Training."}
    )
    dpo_beta: Optional[float] = field(
        default=0.1, metadata={"help": "The beta parameter for the DPO loss."}
    )

    def __post_init__(self):
        if isinstance(
            self.lora_target, str
        ):  # support custom target modules/layers of LoRA
            self.lora_target = [
                target.strip() for target in self.lora_target.split(",")
            ]

        if (
            self.num_layer_trainable > 0
        ):  # fine-tuning the last n layers if num_layer_trainable > 0
            trainable_layer_ids = [
                self.num_hidden_layers - k - 1 for k in range(self.num_layer_trainable)
            ]
        else:  # fine-tuning the first n layers if num_layer_trainable < 0
            trainable_layer_ids = [k for k in range(-self.num_layer_trainable)]

        self.trainable_layers = [
            "{:d}.{}".format(idx, self.name_module_trainable)
            for idx in trainable_layer_ids
        ]

        assert self.finetuning_type in [
            "lora",
            "freeze",
            "full",
            "none",
        ], "Invalid fine-tuning method."

    def save_to_json(self, json_path: str):
        r"""Saves the content of this instance in JSON format inside `json_path`."""
        json_string = json.dumps(asdict(self), indent=2, sort_keys=True) + "\n"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_string)

    @classmethod
    def load_from_json(cls, json_path: str):
        r"""Creates an instance from the content of `json_path`."""
        with open(json_path, "r", encoding="utf-8") as f:
            text = f.read()
        return cls(**json.loads(text))


@dataclass
class TrainingArguments(Seq2SeqTrainingArguments):
    cache_dir: Optional[str] = field(default=None)
    train_on_source: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Whether to train on the input in addition to the target text."
        },
    )
    full_finetune: bool = field(
        default=False, metadata={"help": "Finetune the entire model without adapters."}
    )
    do_train: bool = field(
        default=True,
        metadata={"help": "To train or not to train, that is the question?"},
    )
    sample_generate: bool = field(
        default=False, metadata={"help": "If do sample generation on evaluation."}
    )
    optim: str = field(
        default="paged_adamw_32bit", metadata={"help": "The optimizer to be used"}
    )
    max_grad_norm: float = field(
        default=0.3,
        metadata={
            "help": "Gradient clipping max norm. This is tuned and works well for all models tested."
        },
    )
    gradient_checkpointing: bool = field(
        default=True,
        metadata={"help": "Use gradient checkpointing. You want to use this."},
    )
    predict_with_generate: bool = field(
        default=False,
        metadata={
            "help": "Group sequences into batches with same length. Saves memory and speeds up training considerably."
        },
    )
    model_max_length: int = field(
        default=2048,
        metadata={
            "help": "Maximum sequence length. Sequences will be right padded (and possibly truncated)."
        },
    )
    output_dir: str = field(
        default=ADAPTER_PATH,
        metadata={"help": "The output dir for logs and checkpoints"},
    )
    per_device_train_batch_size: int = field(
        default=1,
        metadata={
            "help": "The training batch size per GPU. Increase for better speed."
        },
    )
    gradient_accumulation_steps: int = field(
        default=16,
        metadata={
            "help": "How many gradients to accumulate before to perform an optimizer step"
        },
    )
    max_steps: int = field(
        default=10000, metadata={"help": "How many optimizer update steps to take"}
    )
    # use lora dropout instead for regularization if needed
    weight_decay: float = field(
        default=0.0, metadata={"help": "The L2 weight decay rate of AdamW"}
    )
    learning_rate: float = field(default=0.0002, metadata={"help": "The learnign rate"})
    remove_unused_columns: bool = field(
        default=False,
        metadata={"help": "Removed unused columns. Needed to make this codebase work."},
    )
    lr_scheduler_type: str = field(
        default="constant",
        metadata={
            "help": "Learning rate schedule. Constant a bit better than cosine, and has advantage for analysis"
        },
    )
    warmup_ratio: float = field(
        default=0.03, metadata={"help": "Fraction of steps to do a warmup for"}
    )
    logging_steps: int = field(
        default=10,
        metadata={"help": "The frequency of update steps after which to log the loss"},
    )
    group_by_length: bool = field(
        default=True,
        metadata={
            "help": "Group sequences into batches with same length. Saves memory and speeds up training considerably."
        },
    )
    save_strategy: str = field(
        default="steps", metadata={"help": "When to save checkpoints"}
    )
    save_steps: int = field(default=250, metadata={"help": "How often to save a model"})
    save_total_limit: int = field(
        default=40,
        metadata={
            "help": "How many checkpoints to save before the oldest is overwritten"
        },
    )
