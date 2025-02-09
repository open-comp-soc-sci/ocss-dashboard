.PHONY: yep stop

yep: down build
	docker run -d --name ollama_container --gpus "device=1" -p 11434:11434 ollama/ollama
	# export $(shell grep -v '^#' .env | xargs) && \
	# docker run -d  --gpus all \
	# --name ollama_container \
	# -v ~/.cache/huggingface:/root/.cache/huggingface \
	# --env "HUGGING_FACE_HUB_TOKEN=$$HUGGING_FACE_HUB_TOKEN" \
	# -p 8000:8000 \
	# --ipc=host \
	# vllm/vllm-openai:latest \
	# --model google/gemma-2-27b \
	# --dtype=half \
	# --tensor-parallel-size=2 \
	# --pipeline-parallel-size=2 \
	# --max-num-batched-tokens=8192
	#
	# the above was better
	#
	# docker run -d --gpus "device=1" \
	# 	--name ollama_container \
	# 	-v ~/.cache/huggingface:/root/.cache/huggingface \
	# 	--env "HUGGING_FACE_HUB_TOKEN=$$HUGGING_FACE_HUB_TOKEN" \
	# 	-p 8000:8000 \
	# 	--ipc=host \
	# 	vllm/vllm-openai:latest \
	# 	--model meta-llama/Llama-2-7b-chat-hf
	# make logs
	sleep 3
	docker exec -it ollama_container ollama pull gemma2:27b
	curl http://localhost:11434/api/tags


build:
	docker build -t ollama/ollama .

stop down:
	-docker stop ollama_container && docker rm ollama_container

logs:
	docker logs -f ollama_container