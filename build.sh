set -e

BUILD_PATH='./jp_civil_law/build'

# Load rdflib graph.
echo "==> Run 'python -m jp_civil_law.run'..."
python -m jp_civil_law.run
echo "==> Finished."
echo ""

# Generate graph as PNG.
echo "==> Generate ${BUILD_PATH}/graph.png..."
dot -Tpng "${BUILD_PATH}/graph.dot" > "${BUILD_PATH}/graph.png"
echo "==> Done."
