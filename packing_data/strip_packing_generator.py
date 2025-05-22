#!/usr/bin/env python3
import argparse
import random
import json

def generate_rectangles(num, strip_width, max_length):
    rects = []
    for idx in range(num):
        w = random.randint(1, strip_width)
        L = random.randint(1, max_length)
        rects.append({
            "index":  idx,
            "width":  w,
            "length": L
        })
    return rects

def main():
    parser = argparse.ArgumentParser(
        description="Generate a strip‐packing JSON instance with random rectangles"
    )
    parser.add_argument(
        "-n", "--num", type=int, required=True,
        help="Number of rectangles to generate"
    )
    parser.add_argument(
        "-w", "--strip-width", type=int, required=True,
        help="Width of the strip (max rectangle width)"
    )
    parser.add_argument(
        "-l", "--max-length", type=int, default=20,
        help="Maximum rectangle length (default: 20)"
    )
    parser.add_argument(
        "output",
        help="Output JSON file name"
    )
    args = parser.parse_args()

    data = {
        "strip_width": args.strip_width,
        "rectangles": generate_rectangles(
            args.num, args.strip_width, args.max_length
        )
    }

    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Written {args.output} with {args.num} rectangles.")

if __name__ == "__main__":
    main()
