def kw_only_arg(*, kwo):
    return kwo


def many_kw_only_args(*, first, second, third):
    return first + second + third


def kw_only_arg_with_default(*, kwo="default", another="another"):
    return f"{kwo}-{another}"


def mandatory_after_defaults(*, default1="xxx", mandatory, default2="zzz"):
    return f"{default1}-{mandatory}-{default2}"


def kw_only_arg_with_annotation(*, kwo: str):
    return kwo


def kw_only_arg_with_annotation_and_default(*, kwo: str = "default"):
    return kwo


def kw_only_arg_with_varargs(*varargs, kwo):
    return "-".join([*varargs, kwo])


def all_arg_types(pos_req, pos_def="pd", *varargs, kwo_req, kwo_def="kd", **kwargs):
    kwargs = [f"{k}={kwargs[k]}" for k in sorted(kwargs)]
    return "-".join([pos_req, pos_def, *varargs, kwo_req, kwo_def, *kwargs])
