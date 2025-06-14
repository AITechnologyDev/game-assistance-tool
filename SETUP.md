# Advanced Setup Guide

## 1. Model Installation
```bash
# Create models directory
mkdir models

# Download Mistral (recommended)
wget -P models/ https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf

# Or download smaller Phi-2 model
wget -P models/ https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
```

## 2. GPU Acceleration (Optional)
```bash
# Uninstall CPU-only version
pip uninstall llama-cpp-python

# Install CUDA-enabled version
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --no-cache-dir
```

Then in `src/assistant.py`:
```python
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=20,  # Offload 20 layers to GPU
    # ...
)
```

## 3. Game-Specific Configuration
### For CS2
```python
MONEY_REGION = (70, 35, 150, 40)   # Top-left corner
ROUND_REGION = (960, 35, 100, 40)  # Center top
```

### For Valorant
```python
MONEY_REGION = (80, 30, 140, 35)   # Top-left
ROUND_REGION = (950, 30, 90, 35)   # Center top
```

## 4. Performance Tuning
- Reduce AI model size for better performance
- Lower OCR scan frequency in code
- Decrease motion sensitivity:
  ```python
  MIN_MOTION_SIZE = 700  # Higher = fewer detections
  ```

## 5. Troubleshooting
**Problem**: Model not loading  
**Solution**: Ensure correct path in MODEL_PATH

**Problem**: OCR not reading money  
**Solution**: Adjust MONEY_REGION coordinates

**Problem**: High CPU usage  
**Solution**: Use smaller model (Phi-2 or TinyLlama)