# run.py — ручной запуск и примеры FilePathParser

from src.neuro_fsm import NeuroFSM


def main():
    print("=== DEMO: NeuroFSM ===")

    parser = NeuroFSM(
        ["cat", "dog"],
        ["night", "day"],
        date=True,
        time=True,
        patterns={"cam": r"cam\d{1,3}"}
    )

    test_path = "cat_night_cam15_20240619_1236.jpg"
    result = parser.parse(test_path)
    print(f"Parsing: {test_path}")
    print(result)


if __name__ == "__main__":
    main()
