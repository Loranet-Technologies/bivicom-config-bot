#!/bin/bash
# test_build.sh - Automated build testing

echo "🧪 Starting Build Tests..."
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${YELLOW}📋 Testing: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ $test_name: PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ $test_name: FAILED${NC}"
        ((TESTS_FAILED++))
    fi
}

# Test 1: Prerequisites
run_test "Python Version Check" "python3 --version"
run_test "PyInstaller Installation" "pip list | grep pyinstaller"
run_test "Dependencies Check" "pip list | grep -E '(paramiko|plyer)'"

# Test 2: GUI Test (quick launch test)
run_test "GUI Import Test" "python3 -c 'import gui_enhanced; print(\"GUI module imports OK\")'"

# Test 3: Build Scripts Exist
run_test "Build Scripts Exist" "test -f build_standalone.sh && test -f build_cross_platform.sh"

# Test 4: Make Scripts Executable
run_test "Make Scripts Executable" "chmod +x build_standalone.sh build_cross_platform.sh"

# Test 5: Quick Build Test
run_test "Quick Build Test" "./build_standalone.sh"

# Test 6: Verify Build Output
run_test "Build Output Verification" "test -d dist/standalone && ls dist/standalone/ | grep -q Bivicom-Configurator"

# Test 7: File Structure Check
run_test "File Structure Check" "test -f dist/standalone/network_config.sh && test -f dist/standalone/requirements.txt"

# Test 8: Executable Permissions
run_test "Executable Permissions" "test -x dist/standalone/Bivicom-Configurator*"

# Test 9: Network Script Test
run_test "Network Script Help" "cd dist/standalone && ./network_config.sh --help | head -5"

# Test 10: File Size Check
run_test "Executable Size Check" "test \$(stat -f%z dist/standalone/Bivicom-Configurator* 2>/dev/null || stat -c%s dist/standalone/Bivicom-Configurator* 2>/dev/null) -gt 1000000"

echo -e "\n${YELLOW}📊 Test Results Summary${NC}"
echo "=========================="
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Build system is working correctly.${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Some tests failed. Please check the output above.${NC}"
    exit 1
fi
