from scripts.check_dco import has_matching_signoff


def test_matching_dco_signoff():
    assert has_matching_signoff(
        "Improve search\n\nSigned-off-by: Ada Example <ada@example.com>\n",
        "Ada Example",
        "ada@example.com",
    )


def test_dco_signoff_must_match_author_identity():
    message = "Improve search\n\nSigned-off-by: Other Person <other@example.com>\n"
    assert not has_matching_signoff(message, "Ada Example", "ada@example.com")


def test_dco_signoff_is_case_insensitive_for_identity():
    assert has_matching_signoff(
        "Signed-off-by: ADA EXAMPLE <ADA@EXAMPLE.COM>", "Ada Example", "ada@example.com"
    )
