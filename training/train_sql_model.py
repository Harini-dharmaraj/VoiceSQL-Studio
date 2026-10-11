import os
import json
import time
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "google/flan-t5-small"
OUTPUT_DIR = "saved_model"
DATASET_PATH = "training/dataset.json"

SCHEMA_PREFIX = (
    "Translate to SQL for IMDb database (tables: movies, directors, actors, movie_cast, reviews). "
    "Question: "
)

class TextToSqlDataset(Dataset):
    def __init__(self, data, tokenizer, max_input_length=128, max_target_length=128):
        self.data = data
        self.tokenizer = tokenizer
        self.max_input_length = max_input_length
        self.max_target_length = max_target_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        input_text = SCHEMA_PREFIX + item["question"]
        target_text = item["sql"]

        input_enc = self.tokenizer(
            input_text,
            max_length=self.max_input_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        target_enc = self.tokenizer(
            target_text,
            max_length=self.max_target_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        labels = target_enc.input_ids.squeeze()
        labels[labels == self.tokenizer.pad_token_id] = -100  # PyTorch ignore index for loss calculation

        return {
            "input_ids": input_enc.input_ids.squeeze(),
            "attention_mask": input_enc.attention_mask.squeeze(),
            "labels": labels
        }

import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def train_model(epochs=3, batch_size=8, lr=5e-4):
    """
    Fine-tunes Google Flan-T5 on the IMDb Text-to-SQL dataset.
    Saves trained weights to saved_model/ for offline inference.
    """
    print("=" * 60)
    print("[VoiceSQL Studio] Text-to-SQL Neural Model Fine-Tuning")
    print("=" * 60)

    # 1. Device check
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device in use: {device} ({'GPU Acceleration Active' if device.type == 'cuda' else 'CPU Mode (Standard)'})")

    # 2. Check dataset
    if not os.path.exists(DATASET_PATH):
        from training.dataset_generator import generate_training_dataset
        generate_training_dataset(DATASET_PATH)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} training pairs from {DATASET_PATH}")

    # 3. Load Tokenizer & Model
    print(f"\nLoading pre-trained base model: {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    model.to(device)

    # 4. Prepare DataLoader
    dataset = TextToSqlDataset(data, tokenizer)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)

    # 5. Training Loop
    print("\nStarting Supervised Fine-Tuning (SFT)...")
    total_start = time.time()

    model.train()
    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        running_loss = 0.0

        for step, batch in enumerate(loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

        avg_loss = running_loss / len(loader)
        epoch_dur = time.time() - epoch_start
        print(f"Epoch [{epoch}/{epochs}] | Loss: {avg_loss:.4f} | Time: {epoch_dur:.1f}s")

    total_dur = time.time() - total_start
    print(f"\n[DONE] Fine-tuning finished in {total_dur/60:.1f} minutes!")

    # 6. Save Model Checkpoint
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Saving fine-tuned model checkpoint to '{OUTPUT_DIR}/'...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("Model and Tokenizer successfully saved!")

    # 7. Verification Test
    print("\n" + "=" * 60)
    print("[TEST] Verification Test on Unseen Phrasing")
    print("=" * 60)
    test_queries = [
        "show the actors who were born on the year 1956",
        "show all the American actors",
        "movies released on 2008",
        "show lengthy blockbuster movies",
        "which picture collected more",
        "who is the hero of Inception",
        "who is the directer of Oppenheimer",
        "what is the public talk of Inception",
        "movies in netflix ott",
        "Count of movies by streaming platform"
    ]

    model.eval()
    for q in test_queries:
        inp = SCHEMA_PREFIX + q
        inputs = tokenizer(inp, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=128)
        sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Question : {q}")
        print(f"Model SQL: {sql}")
        print("-" * 50)

if __name__ == "__main__":
    train_model(epochs=3, batch_size=8, lr=5e-4)
