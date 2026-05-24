#!/bin/bash
# ⚡ Tesla Coil Optimizer (TCO) - Reference Repositories Fetch Script
# Engineered by Dexmond Technologies for dynamic developer environment staging.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REF_DIR="$ROOT_DIR/reference_repos"
TOP_REPOS_FILE="$ROOT_DIR/top_repos.txt"

echo "⚡ Staging TCO Open-Source Reference Repositories..."
mkdir -p "$REF_DIR"

if [ ! -f "$TOP_REPOS_FILE" ]; then
    echo "❌ Error: top_repos.txt not found at $TOP_REPOS_FILE"
    exit 1
fi

while IFS= read -r repo_url || [ -n "$repo_url" ]; do
    # Strip whitespace
    repo_url=$(echo "$repo_url" | xargs)
    
    # Skip empty lines or comments
    if [ -z "$repo_url" ] || [[ "$repo_url" =~ ^# ]]; then
        continue
    fi
    
    # Extract repo name from URL
    repo_name=$(basename "$repo_url" .git)
    target_path="$REF_DIR/$repo_name"
    
    if [ -d "$target_path/.git" ]; then
        echo "🔄 Updating reference: $repo_name..."
        cd "$target_path" && git pull --ff-only || echo "⚠️ Warning: Failed to update $repo_name, skipping."
    else
        echo "📥 Cloning reference: $repo_name..."
        git clone "$repo_url" "$target_path" || echo "⚠️ Warning: Failed to clone $repo_name, skipping."
    fi
done < "$TOP_REPOS_FILE"

echo "✅ Reference repositories successfully synchronized in reference_repos/!"
