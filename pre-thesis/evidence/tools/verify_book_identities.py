#!/usr/bin/env python3
"""Apply and check the 2026-09-09 identity audit for material/books/.

The audit is intentionally limited to bibliographic identity.  It does not
promote a source into ``references/LITERATURE_LEDGER.md`` and it does not
claim that a publisher record supports any scientific statement in the TFM.
The curated consultation decisions, claim links, hashes, and copyright notes
remain untouched.
"""

from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BOOK_MAP = REPO_ROOT / "pre-thesis" / "evidence" / "book-consultation-map.csv"
VERIFICATION_DATE = "2026-09-09"
NEW_COLUMNS = ("verification_source", "verification_date", "verification_note")


# Records were checked against the linked publisher, DOI, journal, preprint, or
# institutional catalog and against the legal/title pages of the local unit.
# ``identity=None`` preserves the already verified ledger identity verbatim.
AUDIT: dict[str, dict[str, str | None]] = {
    "SRC-617a593591cb7e13": {
        "status": "verified-ledger:chenRen2020AverageTracking",
        "source": "https://doi.org/10.1007/978-3-030-39536-0",
        "identity": None,
        "note": "Springer/DOI and local edition agree.",
    },
    "SRC-c68ccfd92d3f5d54": {
        "status": "verified-ledger:rozaMaggioreScardovi2022Coordination",
        "source": "https://doi.org/10.1007/978-3-030-96087-2",
        "identity": None,
        "note": "Springer/DOI and local edition agree.",
    },
    "SRC-a5352edb4fdf3762": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-030-95029-3",
        "identity": "Lei Ding, Qing-Long Han y Boda Ning; Distributed Control and Optimization of Networked Microgrids: A Multi-Agent System Based Approach; Springer Cham; 1.ª ed.; 2022; ISBN 978-3-030-95028-6; DOI 10.1007/978-3-030-95029-3",
        "note": "Identidad cerrada en la ficha Springer; no está de alta en el ledger.",
    },
    "SRC-eb06edb5b9fef4df": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-319-45150-3",
        "identity": "Yuanqing Wu, Renquan Lu, Hongye Su, Peng Shi y Zheng-Guang Wu; Synchronization Control for Large-Scale Network Systems; Springer Cham; 1.ª ed.; 2017; ISBN 978-3-319-45149-7; DOI 10.1007/978-3-319-45150-3",
        "note": "La ficha Springer resuelve el año que faltaba.",
    },
    "SRC-d366d50beff01df1": {
        "status": "verified-publisher",
        "source": "https://www.sciencedirect.com/book/9780128183656/consensus-tracking-of-multi-agent-systems-with-switching-topologies",
        "identity": "Lijing Dong y Sing Kiong Nguang; Consensus Tracking of Multi-Agent Systems with Switching Topologies; Academic Press; 1.ª ed.; 2020; ISBN 978-0-12-818365-6",
        "note": "Identidad contrastada con el catálogo ScienceDirect y la página legal local.",
    },
    "SRC-e385619b26baf1b7": {
        "status": "verified-publisher",
        "source": "https://www.routledge.com/Robust-Cooperative-Control-of-Multi-Agent-Systems-A-Prediction-and-Observation-Prospective/Wang-Zuo-Wang-Ding/p/book/9780367758233",
        "identity": "Chunyan Wang, Zongyu Zuo, Jianan Wang y Zhengtao Ding; Robust Cooperative Control of Multi-Agent Systems: A Prediction and Observation Prospective; CRC Press; 1.ª ed.; 2021; ISBN 978-0-367-75822-6; DOI 10.1201/9781003164142",
        "note": "Se corrige Perspective por el título editorial Prospective; se ignora el Subject corrupto del PDF.",
    },
    "SRC-72cf71b8d4c2f78a": {
        "status": "verified-publisher",
        "source": "https://www.routledge.com/Control-and-State-Estimation-for-Dynamical-Network-Systems-with-Complex-Samplings/Shen-Wang-Li/p/book/9781032310206",
        "identity": "Bo Shen, Zidong Wang y Qi Li; Control and State Estimation for Dynamical Network Systems with Complex Samplings; CRC Press; 1.ª ed.; 2023; ISBN 978-1-032-30996-5; DOI 10.1201/9781003307648",
        "note": "La página legal local dice First edition published 2023; el nombre del archivo indica 2022.",
    },
    "SRC-ae2579b85f790469": {
        "status": "verified-publisher",
        "source": "https://doi.org/10.1201/b17571",
        "identity": "Zhongkui Li y Zhisheng Duan; Cooperative Control of Multi-Agent Systems: A Consensus Region Approach; CRC Press; 1.ª ed.; 2015; ISBN 978-1-4665-6997-3; DOI 10.1201/b17571",
        "note": "La copia tiene fecha de producción 2014 y copyright 2015; se usa el año bibliográfico 2015.",
    },
    "SRC-e0d36b349fca2523": {
        "status": "verified-publisher",
        "source": "https://www.worldscientific.com/worldscibooks/10.1142/Q0307",
        "identity": "Jeremy Pitt; Self-Organising Multi-Agent Systems: Algorithmic Foundations of Cyber-Anarcho-Socialism; World Scientific; 2021; ISBN 978-1-80061-042-2; DOI 10.1142/Q0307",
        "note": "El catálogo/DOI usa 2021; la página legal de la copia muestra copyright 2022.",
    },
    "SRC-029958c43a90def4": {
        "status": "verified-publisher",
        "source": "https://www.oreilly.com/library/view/learning-javascript-design/9781098139865/",
        "identity": "Addy Osmani; Learning JavaScript Design Patterns: A JavaScript and React Developer's Guide; 2.ª ed.; O'Reilly Media; 2023; ISBN 978-1-098-13987-2",
        "note": "Identidad cerrada; la decisión out-of-scope se conserva.",
    },
    "SRC-7923e0f353c892cb": {
        "status": "verified-publisher",
        "source": "https://www.intechopen.com/books/7227",
        "identity": "Efren Gorrostieta Hurtado, editor; Applications of Mobile Robots; IntechOpen; 2019; ISBN 978-1-78985-756-6; DOI 10.5772/intechopen.74181",
        "note": "Se sustituye la identidad inferida y el DOI de un capítulo por la ficha del volumen.",
    },
    "SRC-f77a1852b0dd9547": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-981-97-0968-7",
        "identity": "Guanglei Zhao, Hailong Cui, Changchun Hua y Shuang Liu; Cooperative Control of Multi-Agent Systems: A Hybrid System Approach; Springer Singapore; 1.ª ed.; 2024; ISBN 978-981-97-0967-0; DOI 10.1007/978-981-97-0968-7",
        "note": "Springer/DOI y la página legal local concuerdan.",
    },
    "SRC-9b99df00a9de8dbe": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-030-98377-2",
        "identity": "He Cai, Youfeng Su y Jie Huang; Cooperative Control of Multi-Agent Systems: Distributed-Observer and Distributed-Internal-Model Approaches; Springer Cham; 1.ª ed.; 2022; ISBN 978-3-030-98376-5; DOI 10.1007/978-3-030-98377-2",
        "note": "Identidad cerrada en la ficha Springer; no está de alta en el ledger.",
    },
    "SRC-ba119b1e62a727e3": {
        "status": "verified-journal-doi",
        "source": "https://doi.org/10.1109/ACCESS.2018.2890086",
        "identity": "Yunhua Wu, Mohong Zheng, Mengjie He, Dawei Zhang, Wei He, Bing Hua, Zhiming Chen y Feng Wang; Cooperative Game Theory-Based Optimal Angular Momentum Management of Hybrid Attitude Control Actuator; IEEE Access, 7, 6853-6865; 2019; DOI 10.1109/ACCESS.2018.2890086",
        "note": "Artículo verificado por DOI y ficha de IEEE Access; permanece out-of-scope.",
    },
    "SRC-d7808bdf107394b0": {
        "status": "verified-ledger:bullo2009distributed",
        "source": "https://doi.org/10.1515/9781400831470",
        "identity": None,
        "note": "DOI editorial y entrada del ledger concuerdan.",
    },
    "SRC-6fdf8c2acc16ef8a": {
        "status": "verified-publisher",
        "source": "https://doi.org/10.1201/9781003394372",
        "identity": "Wei Wang, Jiang Long, Jiangshuai Huang y Changyun Wen; Distributed Adaptive Consensus Control of Uncertain Multi-Agent Systems; CRC Press; 1.ª ed.; 2025; ISBN 978-1-032-49546-0; DOI 10.1201/9781003394372",
        "note": "La página legal del adelanto editorial fija 2025; los escaparates muestran fechas de disponibilidad distintas.",
    },
    "SRC-bf8f10d20534d125": {
        "status": "verified-ledger:renBeard2008Consensus",
        "source": "https://doi.org/10.1007/978-1-84800-015-5",
        "identity": None,
        "note": "Springer/DOI y entrada del ledger concuerdan.",
    },
    "SRC-9752523ef477dbb6": {
        "status": "verified-publisher",
        "source": "https://www.cambridge.org/core/books/games-and-coalitions/3F59298409B0E267B4F9C19A1B1D9ADE",
        "identity": "Akira Okada; Games and Coalitions: Bridging Non-cooperative and Cooperative Approaches; Cambridge University Press; 2026; ISBN 978-1-009-72901-7; DOI 10.1017/9781009729017",
        "note": "Identidad cerrada en Cambridge Core; cualquier uso posterior requiere alta en el ledger.",
    },
    "SRC-cc14c73b30364a27": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-031-27601-9",
        "identity": "Uri Weiss y Joseph Agassi; Games to Play and Games Not to Play: Strategic Decisions via Extensions of Game Theory; Springer Cham; 1.ª ed.; 2023; ISBN 978-3-031-27600-2; DOI 10.1007/978-3-031-27601-9",
        "note": "Identidad cerrada; la decisión out-of-scope se conserva.",
    },
    "SRC-e826761b9b60501e": {
        "status": "verified-ledger:martinezPiazuelo2026GNEBook",
        "source": "https://doi.org/10.1007/978-3-032-06081-5",
        "identity": None,
        "note": "Springer/DOI y entrada del ledger concuerdan.",
    },
    "SRC-36d7e7ffdbd50096": {
        "status": "verified-publisher",
        "source": "https://www.sciencedirect.com/book/9780323901314/second-order-consensus-of-continuous-time-multi-agent-systems",
        "identity": "Huaqing Li, Dawen Xia, Qingguo Lü, Zheng Wang, Xiangzhao Wu, Huiwei Wang y Lianghao Ji; Second-Order Consensus of Continuous-Time Multi-Agent Systems; Academic Press; 2021; ISBN 978-0-323-90131-4; DOI 10.1016/C2020-0-03380-3",
        "note": "Identidad contrastada con el catálogo ScienceDirect y la copia local.",
    },
    "SRC-4ced4ee03f6d46a6": {
        "status": "verified-ledger:siegwartNourbakhsh2004Autonomous",
        "source": "https://mitpress.mit.edu/9780262195027/introduction-to-autonomous-mobile-robots/",
        "identity": None,
        "note": "La unidad es la primera edición de 2004, no la segunda de 2011.",
    },
    "SRC-d872978ac0bf7e48": {
        "status": "verified-publisher",
        "source": "https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/copyright-page01.html",
        "identity": "Martin Kleppmann; Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems; O'Reilly Media; 1.ª ed.; 2017; ISBN 978-1-449-37332-0",
        "note": "La página legal editorial fija marzo de 2017; el nombre local indica 2018.",
    },
    "SRC-097398c064adff1a": {
        "status": "verified-ledger-as-preprint:lee2025switching",
        "source": "https://arxiv.org/abs/2511.22810",
        "identity": None,
        "note": "Se conserva explícitamente el estado de preprint, no publicación revisada por pares.",
    },
    "SRC-9afea5b640d8009e": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-031-40180-0",
        "identity": "Dmitrii Lozovanu y Stefan Wolfgang Pickl; Markov Decision Processes and Stochastic Positional Games: Optimal Control on Complex Networks; Springer Cham; 1.ª ed.; 2024; ISBN 978-3-031-40179-4; DOI 10.1007/978-3-031-40180-0",
        "note": "Springer/DOI y la unidad local concuerdan.",
    },
    "SRC-2db0fd66bf8a128b": {
        "status": "verified-publisher",
        "source": "https://doi.org/10.1201/9781003098607",
        "identity": "Julian Barreiro-Gomez y Hamidou Tembine; Mean-Field-Type Games for Engineers; CRC Press; 1.ª ed.; 2022; ISBN 978-0-367-56612-8; DOI 10.1201/9781003098607",
        "note": "La página legal fija primera edición 2022; el nombre local indica 2021.",
    },
    "SRC-6140ef0a5f2b1f0b": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-031-26564-8",
        "identity": "Ahmad Taher Azar, Ibraheem Kasim Ibraheem y Amjad Jaleel Humaidi, editores; Mobile Robot: Motion Control and Path Planning; Springer Cham; 1.ª ed.; 2023; ISBN 978-3-031-26563-1; DOI 10.1007/978-3-031-26564-8",
        "note": "Identidad del volumen cerrada; los capítulos que se citen deberán verificarse por separado.",
    },
    "SRC-0b7ceba994fe5772": {
        "status": "verified-ledger:yildirimReefkeAktas2023Warehouse",
        "source": "https://doi.org/10.1007/978-3-031-12307-8",
        "identity": None,
        "note": "Palgrave/DOI y entrada del ledger concuerdan.",
    },
    "SRC-c0cae4da012e4a4e": {
        "status": "verified-publisher",
        "source": "https://www.intechopen.com/books/12723",
        "identity": "Serdar Küçük, editor; Multi-Robot Systems - New Advances; IntechOpen; 2023; ISBN 978-1-83768-289-8; DOI 10.5772/intechopen.108092",
        "note": "Se resuelve el contenedor y se descarta el metadato Author contaminado del PDF.",
    },
    "SRC-6ced88da54848d51": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-031-43575-1",
        "identity": "Julio B. Clempner y Alexander Poznyak; Optimization and Games for Controllable Markov Chains: Numerical Methods with Application to Finance and Engineering; Springer Cham; 1.ª ed.; 2024; ISBN 978-3-031-43574-4; DOI 10.1007/978-3-031-43575-1",
        "note": "Se confirma que Janusz Kacprzyk es editor de serie y no autor del volumen.",
    },
    "SRC-3521ec0ec24d75f2": {
        "status": "verified-publisher",
        "source": "https://www.sciencedirect.com/book/9780128211861/advanced-distributed-consensus-for-multiagent-systems",
        "identity": "Magdi S. Mahmoud, Mojeed O. Oyedeji y Yuanqing Xia; Advanced Distributed Consensus for Multiagent Systems; Academic Press; 2021; ISBN 978-0-12-821186-1; DOI 10.1016/C2019-0-03211-6",
        "note": "Identidad contrastada con el catálogo ScienceDirect y la unidad local.",
    },
    "SRC-8e9b346a98c3d2f5": {
        "status": "verified-publisher",
        "source": "https://doi.org/10.1201/9781003180982",
        "identity": "Guanghui Wen, Wenwu Yu, Yuezu Lv y Peijun Wang; Cooperative Control of Complex Network Systems with Dynamic Topologies; CRC Press; 1.ª ed.; 2021; ISBN 978-1-032-01917-8; DOI 10.1201/9781003180982",
        "note": "La publicación/DOI es de 2021; el escaparate editorial muestra copyright 2022.",
    },
    "SRC-8d35243f573f11d9": {
        "status": "verified-ledger:carriero2026DistributedControl",
        "source": "https://hdl.handle.net/11567/1288096",
        "identity": None,
        "note": "Repositorio institucional y entrada del ledger concuerdan.",
    },
    "SRC-cd6f9eaf695787a8": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-031-15226-9",
        "identity": "José M. Cascalho, Mohammad Osman Tokhi, Manuel F. Silva, Armando Mendes, Khaled Goher y Matthias Funk, editores; Robotics in Natural Settings: CLAWAR 2022; Springer Cham; LNNS 530; 2023; ISBN 978-3-031-15225-2; DOI 10.1007/978-3-031-15226-9",
        "note": "Identidad del volumen de actas cerrada; permanece out-of-scope como fuente global.",
    },
    "SRC-fda513c2ae72b910": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-031-22562-8",
        "identity": "Santosh Kumar Yadav; Advanced Graph Theory; Springer Cham; 1.ª ed.; 2023; ISBN 978-3-031-22561-1; DOI 10.1007/978-3-031-22562-8",
        "note": "Springer/DOI y la unidad local concuerdan.",
    },
    "SRC-7c9c92629c5a9197": {
        "status": "verified-publisher",
        "source": "https://link.springer.com/book/10.1007/978-3-031-07051-8",
        "identity": "Valery Y. Glizer y Oleg Kelis; Singular Linear-Quadratic Zero-Sum Differential Games and H-infinity Control Problems: Regularization Approach; Birkhäuser Cham; 1.ª ed.; 2022; ISBN 978-3-031-07050-1; DOI 10.1007/978-3-031-07051-8",
        "note": "Identidad cerrada; la decisión out-of-scope se conserva.",
    },
    "SRC-7df2a947e484a325": {
        "status": "verified-ledger:quijano2017population",
        "source": "https://doi.org/10.1109/MCS.2016.2621479",
        "identity": None,
        "note": "DOI de IEEE Control Systems Magazine y entrada del ledger concuerdan.",
    },
}


def render_rows() -> tuple[list[str], list[dict[str, str]]]:
    with BOOK_MAP.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or ())

    unit_ids = {row["unit_id"] for row in rows}
    if unit_ids != set(AUDIT):
        missing = sorted(unit_ids - set(AUDIT))
        extra = sorted(set(AUDIT) - unit_ids)
        raise ValueError(f"Book identity audit coverage mismatch: missing={missing}, extra={extra}")

    for column in NEW_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)

    for row in rows:
        audit = AUDIT[row["unit_id"]]
        row["identity_status"] = str(audit["status"])
        if audit["identity"] is not None:
            row["identity"] = str(audit["identity"])
        row["verification_source"] = str(audit["source"])
        row["verification_date"] = VERIFICATION_DATE
        row["verification_note"] = str(audit["note"])

    return fieldnames, rows


def render_csv() -> str:
    fieldnames, rows = render_rows()
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when the curated CSV is stale")
    args = parser.parse_args()

    expected = render_csv()
    if args.check:
        current = BOOK_MAP.read_text(encoding="utf-8-sig")
        if current != expected:
            print(f"STALE: {BOOK_MAP.relative_to(REPO_ROOT)}")
            return 1
        print(f"OK: 37/37 book identities verified as of {VERIFICATION_DATE}")
        return 0

    BOOK_MAP.write_text("\ufeff" + expected, encoding="utf-8", newline="")
    print(f"WROTE: {BOOK_MAP.relative_to(REPO_ROOT)} (37 verified identities)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
