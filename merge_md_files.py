import os
import glob

def merge_markdown_files():
    policy_dir = "libs/policy/"  # Path to the policy directory
    output_filename = "merged_policies.md" # Output file in the current directory
    
    # Ensure the policy directory exists
    if not os.path.isdir(policy_dir):
        print(f"Error: Directory not found at {os.path.abspath(policy_dir)}")
        return

    # Get all .md files directly under the policy_dir
    # os.path.join(policy_dir, '*.md') will create a pattern like "libs/policy/*.md"
    md_files = glob.glob(os.path.join(policy_dir, '*.md'))
    
    # Sort files to ensure a consistent order (optional, but good practice)
    md_files.sort()

    if not md_files:
        print(f"No .md files found in {os.path.abspath(policy_dir)}")
        return

    print(f"Found {len(md_files)} .md files to merge.")

    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for filepath in md_files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(f"\n\n--- Merged from: {filename} ---\n\n")
                    outfile.write(content)
                print(f"Successfully merged: {filename}")
            except Exception as e:
                print(f"Error reading or writing file {filename}: {e}")

    print(f"All .md files have been merged into: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    merge_markdown_files() 