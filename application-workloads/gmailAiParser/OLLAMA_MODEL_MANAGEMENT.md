# Ollama Model Management Guide

## Managing Models in Open WebUI

### Disable Models in Open WebUI (Don't Delete from Ollama)

**In Open WebUI Settings:**
1. Click **Settings** (gear icon)
2. Go to **Models** tab
3. Find models you want to hide
4. Toggle them **OFF** to disable
5. They'll remain on your system but won't appear in Open WebUI

**Note:** This only hides them from the UI, doesn't remove them from disk.

---

## Actually Removing Models from Ollama

### Check Current Models
```bash
ollama list
```

### Remove Models You Don't Need
```bash
# Remove a specific model
ollama rm <model-name>

# Examples:
ollama rm llama3.1:70b     # Large model you don't need
ollama rm codellama        # If not coding
ollama rm llava            # If not using vision
```

### Which Models to Keep for Gmail Job Parser

**Essential (Keep These):**
```bash
llama3.2:1b    # 1.3GB - Fast detection
llama3.2:3b    # 2.0GB - Balanced extraction
mistral        # 4.1GB - Alternative for testing
```

**Recommended for Testing:**
```bash
phi3:mini      # 2.3GB - Efficient alternative
gemma:2b       # 1.6GB - Google small model
```

**Optional (Only if you have space):**
```bash
llama3.1:8b    # 4.7GB - High accuracy
gemma:7b       # 5.0GB - Google medium
```

**Can Safely Remove:**
- ❌ Code models (codellama, deepseek-coder) - not needed for job parsing
- ❌ Vision models (llava, bakllava) - we're parsing text only
- ❌ Very large models (70B+) - overkill for this use case
- ❌ Language-specific models - if you don't need them

---

## Recommended Setup for Gmail Job Parser

### Minimal Setup (5GB total)
```bash
# Keep only these 3 models
ollama pull llama3.2:1b    # 1.3GB
ollama pull llama3.2:3b    # 2.0GB
ollama pull mistral        # 4.1GB

# Remove everything else
ollama list | grep -v "llama3.2\|mistral\|NAME" | awk '{print $1}' | xargs -I {} ollama rm {}
```

### Balanced Setup (10GB total)
```bash
# Keep these 5 models for comprehensive testing
ollama pull llama3.2:1b    # 1.3GB
ollama pull llama3.2:3b    # 2.0GB
ollama pull mistral        # 4.1GB
ollama pull phi3:mini      # 2.3GB
ollama pull gemma:2b       # 1.6GB
```

### Full Testing Setup (15GB total)
```bash
# All recommended models for CAB validation
ollama pull llama3.2:1b    # 1.3GB
ollama pull llama3.2:3b    # 2.0GB
ollama pull llama3.1:8b    # 4.7GB
ollama pull mistral        # 4.1GB
ollama pull phi3:mini      # 2.3GB
ollama pull gemma:2b       # 1.6GB
ollama pull gemma:7b       # 5.0GB
```

---

## Check Disk Usage

### See Model Sizes
```bash
ollama list
```

### See Total Ollama Storage
```bash
# Linux/Mac
du -sh ~/.ollama

# Find large models
du -sh ~/.ollama/models/blobs/* | sort -h | tail -10
```

### Free Up Space
```bash
# Remove unused models
ollama rm <model-name>

# Remove ALL models (nuclear option)
# WARNING: This deletes everything!
rm -rf ~/.ollama/models/*
```

---

## Quick Commands

### List Models
```bash
ollama list
```

### Pull a Model
```bash
ollama pull llama3.2:3b
```

### Remove a Model
```bash
ollama rm llama3.2:70b
```

### Check if Model Exists
```bash
ollama list | grep "mistral"
```

### Remove All Models Except Specific Ones
```bash
# Keep only llama3.2:1b, llama3.2:3b, and mistral
ollama list | grep -v "llama3.2:1b\|llama3.2:3b\|mistral\|NAME" | awk '{print $1}' | xargs -I {} ollama rm {}
```

---

## For CAB Validation

**Minimum Required:**
- 5 different models (for comprehensive comparison)
- At least 1 non-Llama model (Mistral, Phi3, or Gemma)
- Total size: ~10-15GB

**Recommended Models:**
1. llama3.2:1b (ultra-small benchmark)
2. llama3.2:3b (small benchmark)
3. mistral (non-Llama alternative)
4. phi3:mini (Microsoft efficiency test)
5. gemma:2b OR gemma:7b (Google comparison)

**Optional Additions:**
- llama3.1:8b (if you want to test large models)
- qwen2:7b (if you want to test reasoning)

---

## Open WebUI vs Ollama CLI

**Open WebUI:**
- Visual interface for chatting with models
- Can disable models from appearing in UI
- Doesn't actually remove models from disk

**Ollama CLI:**
- Command-line tool
- `ollama rm` actually deletes models from disk
- `ollama list` shows what's really installed

**For our job parser:**
- We use Ollama API directly (not Open WebUI)
- Open WebUI settings don't affect our code
- You can disable models in Open WebUI if you want
- But you'll still use `ollama rm` to free disk space

---

## Quick Cleanup Script

Save as `cleanup-models.sh`:

```bash
#!/bin/bash
# Keep only models needed for Gmail Job Parser

KEEP_MODELS=(
    "llama3.2:1b"
    "llama3.2:3b"
    "mistral"
    "phi3:mini"
    "gemma:2b"
)

echo "Models to KEEP:"
for model in "${KEEP_MODELS[@]}"; do
    echo "  ✓ $model"
done

echo ""
echo "Models to REMOVE:"

ollama list | tail -n +2 | while read -r line; do
    model=$(echo "$line" | awk '{print $1}')

    if [[ ! " ${KEEP_MODELS[@]} " =~ " ${model} " ]]; then
        echo "  ✗ $model"
    fi
done

echo ""
read -p "Remove unlisted models? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    ollama list | tail -n +2 | while read -r line; do
        model=$(echo "$line" | awk '{print $1}')

        if [[ ! " ${KEEP_MODELS[@]} " =~ " ${model} " ]]; then
            echo "Removing $model..."
            ollama rm "$model"
        fi
    done

    echo "✓ Cleanup complete!"
else
    echo "Cancelled."
fi
```

Usage:
```bash
chmod +x cleanup-models.sh
./cleanup-models.sh
```

---

## Summary

**To disable in Open WebUI:** Settings → Models → Toggle OFF
**To actually remove:** `ollama rm <model-name>`
**For job parser:** Keep 5-7 models (~10-15GB total)
**For CAB approval:** Need at least 5 different models including non-Llama alternatives
