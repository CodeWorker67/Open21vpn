"""Извлечь из лога sync_panel_to_db изменения subscribtion."""
import re
import sys
from pathlib import Path

LOG_CANDIDATES = [
    Path(__file__).resolve().parent / "logs",
    Path(r"C:\Users\nusht\.cursor\projects\c-Users-nusht-PycharmProjects-PortfolioFreelance-BotForSale-Elvis-21OpenVPN\agent-tools\15f1c7b3-dff5-46da-a595-709a3fb9075f.txt"),
]

DEFAULT_LOG = Path(
    r"C:\Users\nusht\.cursor\projects\c-Users-nusht-PycharmProjects-PortfolioFreelance-BotForSale-Elvis-21OpenVPN\agent-tools\15f1c7b3-dff5-46da-a595-709a3fb9075f.txt"
)

PAT = re.compile(r"subscribtion: user_id=(\d+) '([^']*)' -> '([^']*)'")


def main() -> None:
    log_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LOG
    if not log_path.is_file():
        raise SystemExit(f"Log not found: {log_path}")

    rows = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = PAT.search(line)
        if m:
            rows.append((m.group(1), m.group(2), m.group(3)))

    out = Path(__file__).resolve().parent / "sync_subscribtion_changes.txt"
    with out.open("w", encoding="utf-8") as f:
        f.write(f"Всего обновлений subscribtion: {len(rows)}\n\n")
        f.write(f"{'user_id':<14} {'было':<45} {'стало':<20}\n")
        f.write("-" * 82 + "\n")
        for uid, old, new in rows:
            old_disp = "(пусто)" if old in ("None", "") else old
            f.write(f"{uid:<14} {old_disp:<45} {new:<20}\n")

    empty = sum(1 for _, o, _ in rows if o in ("None", ""))
    other = len(rows) - empty
    print(f"Записей: {len(rows)}")
    print(f"Файл: {out}")
    print(f"Было пусто: {empty}, было другое значение: {other}")
    if other:
        print("\nС непустым «было»:")
        for uid, old, new in rows:
            if old not in ("None", ""):
                print(f"  {uid}: {old!r} -> {new!r}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
