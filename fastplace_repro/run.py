import argparse
import os
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from netlist import load_netlist
from placer import place
from metrics import net_hpwl, total_overlap_area, overlap_ratio
from viz import plot_layout


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(here, "config.yaml"))
    ap.add_argument("--netlist", default=os.path.join(here, "data", "toy.json"))
    ap.add_argument("--out", default=os.path.join(here, "layout.png"))
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    nl = load_netlist(args.netlist)
    initial_overlap = total_overlap_area(nl)

    history = place(nl, cfg)

    pos = {c.id: (c.x, c.y) for c in nl.cells.values()}
    print("HPWL         :", round(net_hpwl(nl, pos), 4))
    print("overlap area :", round(total_overlap_area(nl), 4))
    print("overlap ratio:", round(overlap_ratio(nl), 4))
    print("initial overlap:", round(initial_overlap, 4))

    plot_layout(nl, history, args.out)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
