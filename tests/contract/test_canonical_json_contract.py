from decimal import Decimal

from triggertrade.canonical_json import canonical_json_bytes, canonical_json_digest


def test_canonical_json_digest_contract_vectors():
    vectors = [
        (
            {"beta": 2, "alpha": 1},
            b'{"alpha":1,"beta":2}',
            "955c071f4fbee40a01b9bc6e8fb3627e81bda84811ae9c29fcc5812ba3a45162",
        ),
        (
            {"amount": Decimal("751.10"), "raw": "751.10"},
            b'{"amount":751.1,"raw":"751.10"}',
            "fc02e253308030e20213d2cb6f9665f1ce391a51fa53e4503534e6a7984b835f",
        ),
        (
            {"note": "цена €", "ok": True, "missing": None},
            '{"missing":null,"note":"цена €","ok":true}'.encode("utf-8"),
            "3d520fadc9d7e23dd48084489f0051a6c0ceb53aeeb737bd22bcab291a1a5dbf",
        ),
    ]

    for payload, expected_bytes, expected_digest in vectors:
        assert canonical_json_bytes(payload) == expected_bytes
        assert canonical_json_digest(payload) == expected_digest
