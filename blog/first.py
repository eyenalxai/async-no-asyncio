def count_up(*, n: int) -> None:
    for i in range(n):
        print(f"count_up: {i}")


def count_down(*, n: int) -> None:
    for i in range(n, 0, -1):
        print(f"count_dn: {i}")


def main() -> None:
    count_up(n=5)
    count_down(n=5)


if __name__ == "__main__":
    main()
