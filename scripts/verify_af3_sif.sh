#!/usr/bin/env bash
# Validate the rebuilt AF3 v3.0.5 container before swapping it in.
set -uo pipefail
SIF=${1:-/home/user/data/apptainer/alphafold3-v305.sif}
fail=0

chk() { # chk <label> <cmd...>
    local label=$1; shift
    if out=$(timeout 600 "$@" 2>&1); then
        echo "  OK   $label: $out"
    else
        echo "  FAIL $label: $(echo "$out" | tail -3 | tr '\n' ' ')"
        fail=1
    fi
}

echo "== $SIF =="
chk "import" apptainer exec "$SIF" /opt/af3-env/bin/python -c "
import jax, haiku, rdkit, msgpack
from alphafold3.version import __version__
print('af3', __version__, 'jax', jax.__version__, 'haiku', haiku.__version__)
"

# v3.0.5 builds ONE extension, alphafold3/cpp.*.so, exposing submodules as
# attributes -- not per-module .so files. Import it as `alphafold3.cpp`.
chk "cpp ext" apptainer exec "$SIF" /opt/af3-env/bin/python -c "
import alphafold3.cpp as cpp
mods = [m for m in ('cif_dict','mmcif_utils','indexing','mmcif_layout','msa_conversion')
        if hasattr(cpp, m)]
print('cpp submodules:', ','.join(mods))
assert len(mods) == 5, mods
"

# The v3.0.5 performance work added these APIs; their absence means the wheel is
# stale and the speedups we rebuilt for are not actually present.
chk "v305 apis" apptainer exec "$SIF" /opt/af3-env/bin/python -c "
from alphafold3.structure import table, bonds, structure
assert hasattr(table.Table, 'slice_range'), 'Table.slice_range missing'
assert hasattr(bonds.Bonds, 'split_by_atom_ranges'), 'Bonds.split_by_atom_ranges missing'
assert hasattr(structure.Structure, 'filter'), 'Structure.filter missing'
print('slice_range, split_by_atom_ranges, filter present')
"

chk "ccd data" apptainer exec "$SIF" /opt/af3-env/bin/python -c "
from alphafold3.constants import chemical_component_sets
print('ccd sets OK')
"

chk "jax gpu" apptainer exec --nv "$SIF" /opt/af3-env/bin/python -c "
import jax; print(jax.default_backend(), jax.devices()[0].device_kind)
"

# absl's --helpfull exits 1 by design, so assert on its banner instead of status.
entry=$(apptainer exec "$SIF" /opt/af3-env/bin/python /opt/alphafold3/run_alphafold.py --helpfull 2>&1)
if echo "$entry" | grep -q "AlphaFold 3 structure prediction script"; then
    echo "  OK   entrypoint: helpfull banner present"
else
    echo "  FAIL entrypoint: $(echo "$entry" | tail -2 | tr '\n' ' ')"
    fail=1
fi

chk "hmmer patches" apptainer exec "$SIF" bash -c 'grep -c seq_limit /opt/hmmer_bin/*.c 2>/dev/null || jackhmmer -h | grep -c seq_limit'

chk "uv pip check" apptainer exec "$SIF" /opt/uv-env/bin/uv pip check --python /opt/af3-env/bin/python

echo
if [ $fail -eq 0 ]; then echo "ALL CHECKS PASSED"; else echo "SOME CHECKS FAILED"; fi
exit $fail
