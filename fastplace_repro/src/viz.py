import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_layout(netlist, history, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # 左图：布局
    ax = axes[0]
    for net in netlist.nets:
        xs, ys = [], []
        for cid in net.pins:
            c = netlist.cells[cid]
            xs.append(c.x)
            ys.append(c.y)
        if len(xs) >= 2:
            ax.plot(xs, ys, "--", color="lightgray", linewidth=0.8, zorder=1)

    for c in netlist.cells.values():
        color = "tab:red" if c.fixed else "tab:blue"
        ax.add_patch(
            plt.Rectangle(
                (c.x - c.w / 2, c.y - c.h / 2),
                c.w,
                c.h,
                facecolor=color,
                edgecolor="black",
                alpha=0.7,
            )
        )
        ax.text(c.x, c.y, c.id, ha="center", va="center", fontsize=6)

    ax.set_xlim(0, netlist.board_w)
    ax.set_ylim(0, netlist.board_h)
    ax.set_aspect("equal")
    ax.set_title("Global placement")

    # 右图：收敛曲线
    ax2 = axes[1]
    it = [h["iter"] for h in history]
    hp = [h["hpwl"] for h in history]
    ov = [h["overlap"] for h in history]

    ax2.plot(it, hp, "o-", color="tab:blue", label="HPWL")
    ax2.set_xlabel("iteration")
    ax2.set_ylabel("HPWL", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    ax2b = ax2.twinx()
    ax2b.plot(it, ov, "s-", color="tab:orange", label="overlap")
    ax2b.set_ylabel("overlap area", color="tab:orange")
    ax2b.tick_params(axis="y", labelcolor="tab:orange")

    ax2.set_title("Convergence")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
