#!/usr/bin/env bash
# Run vLLM OpenAI-compatible API on host machine.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

HF_HOME="${HF_HOME:-${ROOT_DIR}/.hf-cache}"
mkdir -p "${HF_HOME}"
export HF_HOME
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export TRANSFORMERS_CACHE="${HF_HOME}/transformers"

LLM_MODEL="${LLM_MODEL:-${VLLM_MODEL:-Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4}}"
LLM_HOST="${LLM_HOST:-0.0.0.0}"
LLM_PORT="${LLM_PORT:-8000}"
LLM_API_KEY="${LLM_API_KEY:-sk-local}"
VLLM_GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.92}"
VLLM_MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-1024}"
VLLM_DTYPE="${VLLM_DTYPE:-float16}"
VLLM_MAX_NUM_SEQS="${VLLM_MAX_NUM_SEQS:-8}"
VLLM_MAX_NUM_BATCHED_TOKENS="${VLLM_MAX_NUM_BATCHED_TOKENS:-256}"
ALLOC_CONF_VALUE="${PYTORCH_ALLOC_CONF:-expandable_segments:True}"
export PYTORCH_ALLOC_CONF="${ALLOC_CONF_VALUE}"
# Backward-compatible alias for environments still reading old variable name.
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-${ALLOC_CONF_VALUE}}"

echo "Starting vLLM on ${LLM_HOST}:${LLM_PORT}"
echo "Model: ${LLM_MODEL}"
echo "HF cache: ${HF_HOME}"
echo "gpu_memory_utilization: ${VLLM_GPU_MEMORY_UTILIZATION}"
echo "max_model_len: ${VLLM_MAX_MODEL_LEN}"
echo "max_num_seqs: ${VLLM_MAX_NUM_SEQS}"
echo "max_num_batched_tokens: ${VLLM_MAX_NUM_BATCHED_TOKENS}"

PYTHON_BIN="python3"
if [[ -x "${ROOT_DIR}/.venv-vllm/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv-vllm/bin/python"
fi

exec "${PYTHON_BIN}" -m vllm.entrypoints.openai.api_server \
  --host "${LLM_HOST}" \
  --port "${LLM_PORT}" \
  --model "${LLM_MODEL}" \
  --enforce-eager \
  --max-model-len "${VLLM_MAX_MODEL_LEN}" \
  --max-num-seqs "${VLLM_MAX_NUM_SEQS}" \
  --max-num-batched-tokens "${VLLM_MAX_NUM_BATCHED_TOKENS}" \
  --dtype "${VLLM_DTYPE}" \
  --gpu-memory-utilization "${VLLM_GPU_MEMORY_UTILIZATION}" \
  --api-key "${LLM_API_KEY}"
