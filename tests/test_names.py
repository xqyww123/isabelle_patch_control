from isabelle_patch_control import names


def test_package_names():
    assert names.package_name("expose_foreign") == "isabelle-expose-foreign"
    assert names.package_name("future_assign_interrupt") == "isabelle-future-assign-interrupt"
    assert names.package_name("light_locale") == "isabelle-light-locale"
    assert names.package_name("dev_patches") == "qiyuan-dev-patches"


def test_feature_name_inverts_package_name():
    for f in ("expose_foreign", "future_assign_interrupt", "light_locale", "local_type_abbrev",
              "localized_record", "local_datatype", "dev_patches"):
        assert names.feature_name(names.package_name(f)) == f
    assert names.feature_name("python") is None
