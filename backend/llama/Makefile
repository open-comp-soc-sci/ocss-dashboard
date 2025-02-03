.PHONY: yep

yep:
	export $(shell grep -v '^#' .env | xargs) && \
	docker run --gpus all \
		--name my_vllm_container \
		-v ~/.cache/huggingface:/root/.cache/huggingface \
		--env "HUGGING_FACE_HUB_TOKEN=$$HUGGING_FACE_HUB_TOKEN" \
		-p 8000:8000 \
		--ipc=host \
		vllm/vllm-openai:latest \
		--model meta-llama/Llama-2-7b-chat-hf


stop down:
