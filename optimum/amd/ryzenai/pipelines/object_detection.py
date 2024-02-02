# Copyright 2023 The HuggingFace Team. All rights reserved.
# Licensed under the MIT License.


from transformers import Pipeline
from transformers.image_utils import load_image


class YoloXObjectDetectionPipeline(Pipeline):
    def _sanitize_parameters(self, **kwargs):
        preprocess_params = {}
        if "timeout" in kwargs:
            preprocess_params["timeout"] = kwargs["timeout"]
        postprocess_params = {}
        if "nms_threshold" in kwargs:
            postprocess_params["nms_threshold"] = kwargs["nms_threshold"]
        if "score_threshold" in kwargs:
            postprocess_params["score_threshold"] = kwargs["score_threshold"]
        if "p6" in kwargs:
            postprocess_params["p6"] = kwargs["p6"]
        if "top_k" in kwargs:
            postprocess_params["top_k"] = kwargs["top_k"]
        if "data_format" in kwargs:
            preprocess_params["data_format"] = kwargs["data_format"]
            postprocess_params["data_format"] = kwargs["data_format"]

        return preprocess_params, {}, postprocess_params

    def preprocess(self, image, timeout=None):
        image = load_image(image, timeout=timeout)

        image_features = self.image_processor(image, return_tensors=self.framework)

        return image_features

    def _forward(self, model_inputs):
        ratios = model_inputs.pop("ratios")

        outputs = self.model(**model_inputs)

        model_outputs = {"ratios": ratios, **outputs}

        return model_outputs

    def postprocess(
        self, model_outputs, nms_threshold=0.45, score_threshold=0.1, data_format=None, p6=None, top_k=None
    ):
        ratios = model_outputs.pop("ratios")

        results = []
        outputs = self.image_processor.post_process_object_detection(
            outputs=model_outputs,
            nms_threshold=nms_threshold,
            score_threshold=score_threshold,
            ratios=ratios,
            p6=p6,
            data_format=data_format,
        )[0]

        results = sorted(outputs, key=lambda x: x["score"], reverse=True)
        if top_k:
            results = results[:top_k]

        return results
