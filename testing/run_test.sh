#!/bin/bash

# Accept all arguments as test targets (default to tests/)
TEST_TARGET="${@:-tests/}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MAX_RUNS=30

# 1. Clean old results and restore history
rm -rf allure/api/results/
mkdir -p allure/api/results/history
mkdir -p allure/api/history
mkdir -p allure/api/archive
cp -r allure/api/history/. allure/api/results/history/ 2>/dev/null || true

# 2. Run tests
pytest $TEST_TARGET --alluredir=allure/api/results -v

# 3. Generate the report
allure generate allure/api/results -o allure/api/report --clean

# 4. Save history for next run
cp -r allure/api/report/history/. allure/api/history/

# 4b. Fix buildOrder in history-trend.json
python3 -c "
import json, os

trend_file = 'allure/api/history/history-trend.json'

if os.path.exists(trend_file):
    with open(trend_file, 'r') as f:
        trend = json.load(f)

    for i, entry in enumerate(trend):
        if 'buildOrder' not in entry:
            entry['buildOrder'] = i + 1

    next_order = len(trend) + 1
    trend.append({
        'buildOrder': next_order,
        'data': trend[-1]['data']
    })

    with open(trend_file, 'w') as f:
        json.dump(trend, f, indent=2)

    print(f'✅ buildOrder updated — run {next_order} recorded')
"

# 4c. Copy fixed history back into allure-report so archive has correct trend
cp -r allure/api/history/. allure/api/report/history/

# 5. Archive this run as a full report
cp -r allure/api/report/ allure/api/archive/run_$TIMESTAMP/
echo "✅ Report archived: allure/api/archive/run_$TIMESTAMP/"

# 6. Keep only last 30 runs — delete oldest if exceeded
cd allure/api/archive
RUN_COUNT=$(ls -d run_*/ 2>/dev/null | wc -l)
if [ $RUN_COUNT -gt $MAX_RUNS ]; then
    OLDEST=$(ls -d run_*/ | sort | head -1)
    rm -rf $OLDEST
    echo "🧹 Deleted oldest run: $OLDEST"
fi
cd ../..

# 7. Create shareable ZIP for client
ZIP_NAME="allure-report-$(date +%Y%m%d-%H%M).zip"
rm -f *.zip  # Remove old ZIP files
zip -r $ZIP_NAME allure/api/report/ > /dev/null
ZIP_SIZE=$(ls -lh $ZIP_NAME | awk '{print $5}')
echo "📦 Client report created: $ZIP_NAME ($ZIP_SIZE)"

# 8. Open latest report
allure open allure/api/report &