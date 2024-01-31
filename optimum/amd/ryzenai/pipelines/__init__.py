# Copyright 2023 The HuggingFace Team. All rights reserved.
# Licensed under the MIT License.


from typing import TYPE_CHECKING, Any, Optional, Union

from optimum.exporters import TasksManager
from transformers import ImageClassificationPipeline, Pipeline
from transformers import pipeline as transformers_pipeline
from transformers.image_processing_utils import BaseImageProcessor
from transformers.onnx.utils import get_preprocessor

from ..modeling import RyzenAIModel, RyzenAIModelForImageClassification
from .image_classification import TimmImageClassificationPipeline


if TYPE_CHECKING:
    from transformers.feature_extraction_utils import PreTrainedFeatureExtractor

RYZENAI_SUPPORTED_TASKS = {
    "image-classification": {
        "impl": ImageClassificationPipeline,
        "class": (RyzenAIModelForImageClassification,),
        "default": "amd/resnet50",
        "type": "image",
    }
}


def load_model(
    model,
    task,
    vaip_config,
    SUPPORTED_TASKS,
    token: Optional[Union[bool, str]] = None,
    revision: str = "main",
):
    if model is None:
        model_id = SUPPORTED_TASKS[task]["default"]
        model = SUPPORTED_TASKS[task]["class"][0].from_pretrained(model_id, vaip_config=vaip_config)
    elif isinstance(model, str):
        model_id = model
        ort_model_class = SUPPORTED_TASKS[task]["class"][0]

        model = ort_model_class.from_pretrained(
            model_id,
            vaip_config=vaip_config,
            use_auth_token=token,
            revision=revision,
        )
    elif isinstance(model, RyzenAIModel):
        model_id = None
    else:
        raise ValueError(
            f"""Model {model} is not supported. Please provide a valid model either as string or RyzenAIModel.
            You can also provide non model then a default one will be used"""
        )
    return model, model_id


def pipeline(
    task: str = None,
    model: Optional[Any] = None,
    vaip_config: str = None,
    feature_extractor: Optional[Union[str, "PreTrainedFeatureExtractor"]] = None,
    image_processor: Optional[Union[str, BaseImageProcessor]] = None,
    use_fast: bool = True,
    token: Optional[Union[str, bool]] = None,
    revision: Optional[str] = None,
    **kwargs,
) -> Pipeline:
    model, model_id = load_model(
        model,
        task=task,
        vaip_config=vaip_config,
        SUPPORTED_TASKS=RYZENAI_SUPPORTED_TASKS,
        token=token,
        revision=revision,
    )

    library_name = TasksManager._infer_library_from_model(model)

    if library_name != "timm" and image_processor is None:
        if model_id:
            if feature_extractor is None and image_processor is None:
                image_processor = get_preprocessor(model_id)
        else:
            for preprocessor in model.preprocessors:
                if isinstance(preprocessor, BaseImageProcessor):
                    image_processor = preprocessor
                    break
            if image_processor is None:
                raise ValueError(
                    "Could not automatically find image processor for the RyzenAIModel, you must pass a "
                    "image_processor explictly"
                )

    if task == "image-classification" and library_name == "timm":
        ryzen_pipeline = TimmImageClassificationPipeline
    else:
        ryzen_pipeline = transformers_pipeline

    return ryzen_pipeline(
        task=task,
        model=model,
        feature_extractor=feature_extractor,
        image_processor=image_processor,
        use_fast=use_fast,
        **kwargs,
    )
