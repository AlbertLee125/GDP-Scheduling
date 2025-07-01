# #!/usr/bin/env python3
# import argparse
# import random
# import json

# def generate_rectangles(num, strip_width, max_length):
#     rects = []
#     for idx in range(num):
#         w = random.randint(1, strip_width)
#         L = random.randint(1, max_length)
#         rects.append({
#             "index":  idx,
#             "width":  w,
#             "length": L
#         })
#     return rects


# #  python strip_packing_generator.py -n 16 -w 14 -l 30 strip_packing_rectangle_16.json
# def main():
#     parser = argparse.ArgumentParser(
#         description="Generate a strip‐packing JSON instance with random rectangles"
#     )
#     parser.add_argument(
#         "-n", "--num", type=int, required=True,
#         help="Number of rectangles to generate"
#     )
#     parser.add_argument(
#         "-w", "--strip-width", type=int, required=True,
#         help="Width of the strip (max rectangle width)"
#     )
#     parser.add_argument(
#         "-l", "--max-length", type=int, default=20,
#         help="Maximum rectangle length (default: 20)"
#     )
#     parser.add_argument(
#         "output",
#         help="Output JSON file name"
#     )
#     args = parser.parse_args()

#     data = {
#         "strip_width": args.strip_width,
#         "rectangles": generate_rectangles(
#             args.num, args.strip_width, args.max_length
#         )
#     }

#     with open(args.output, "w") as f:
#         json.dump(data, f, indent=2)
#     print(f"Written {args.output} with {args.num} rectangles.")

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
"""
strip_packing_generator.py

- Default mode (no --batch): behave exactly as your original script.
- --batch mode: emit instances 5→19 × 6→10 in one go.
"""

import argparse, random, json, time
from typing import List, Dict, Any

def generate_rectangles(num: int, strip_width: int, max_length: int) -> List[Dict[str, Any]]:
    rects = []
    for idx in range(num):
        w = random.randint(1, strip_width)
        L = random.randint(1, max_length)
        rects.append({"index": idx, "width": w, "length": L})
    return rects

def single_instance_mode(args):
    data = {
        "strip_width": args.strip_width,
        "rectangles": generate_rectangles(args.num, args.strip_width, args.max_length)
    }
    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Written {args.output} with {args.num} rectangles.")

def batch_mode(args):
    for num in range(5, 20):        # 5 → 19
        for inst in range(6, 11):   # 6 → 10
            if args.seed is not None:
                random.seed(args.seed + num*100 + inst)
            rects = generate_rectangles(num, args.strip_width, args.max_length)
            data = {
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "seed": None if args.seed is None else args.seed + num*100 + inst,
                "strip_width": args.strip_width,
                "rectangles": rects
            }
            fname = f"strip_packing_rectangle_{num}_{inst}.json"
            with open(fname, "w") as f:
                json.dump(data, f, indent=2)
            print(f"→ {fname}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate strip-packing JSON instances (single or batch)."
    )
    parser.add_argument("-n","--num", type=int, help="Number of rectangles (single mode).")
    parser.add_argument("-w","--strip-width", type=int, required=True)
    parser.add_argument("-l","--max-length", type=int, default=20)
    parser.add_argument("--batch", action="store_true",
                        help="Generate all instances for n=5..19, inst=6..10.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed for reproducibility (both modes).")
    parser.add_argument("output", nargs="?",
                        help="Output JSON file (single mode only).")
    args = parser.parse_args()

    if args.batch:
        batch_mode(args)
    else:
        if args.num is None or args.output is None:
            parser.error("In single-instance mode, you must supply -n and output file.")
        single_instance_mode(args)

if __name__ == "__main__":
    main()
