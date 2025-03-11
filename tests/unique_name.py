

from testai.src.interactors.processing.getname import SimpleGetUniqueName


def test_simple():
    result = SimpleGetUniqueName(
        user_id=123
    )

    assert result(".some")


def test_one_dot():
    result = SimpleGetUniqueName(
        user_id=123
    )

    dots = len(result(".some").split(".")) - 1

    assert dots == 1


def test_multiuser():
    result = SimpleGetUniqueName(
        user_id=123
    )

    assert result(".some") != result(".some")
