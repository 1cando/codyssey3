import json
import re
import time


EPSILON = 1e-9
REPEAT_COUNT = 10
SUPPORTED_SIZES = (3, 5, 13, 25)


# --------------------------------------------------
# 1. 공통 유틸리티
# --------------------------------------------------

def normalize_label(label):
    """입력 라벨을 Cross 또는 X로 통일한다."""
    if not isinstance(label, str):
        raise ValueError(f"라벨은 문자열이어야 합니다: {label!r}")

    value = label.strip().lower()

    if value in ("+", "cross"):
        return "Cross"
    if value == "x":
        return "X"

    raise ValueError(f"지원하지 않는 라벨입니다: {label!r}")


def validate_matrix(matrix, expected_size=None, name="배열"):
    """2차원 숫자 배열인지, 행과 열의 크기가 올바른지 검사한다."""
    if not isinstance(matrix, list) or not matrix:
        raise ValueError(f"{name}: 비어 있거나 리스트가 아닙니다.")

    size = len(matrix)

    if expected_size is not None and size != expected_size:
        raise ValueError(
            f"{name}: 행 크기가 일치하지 않습니다. "
            f"기대={expected_size}, 실제={size}"
        )

    for row_index, row in enumerate(matrix):
        if not isinstance(row, list):
            raise ValueError(f"{name}: {row_index + 1}번째 행이 리스트가 아닙니다.")

        if len(row) != size:
            raise ValueError(
                f"{name}: 정사각형 배열이 아닙니다. "
                f"{row_index + 1}번째 행의 열 개수={len(row)}, 기대={size}"
            )

        for column_index, value in enumerate(row):
            # bool은 int의 하위 타입이므로 숫자로 허용하지 않는다.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"{name}: [{row_index}][{column_index}] 값이 숫자가 아닙니다."
                )

    return size


def mac_operation(pattern, filter_matrix):
    """두 배열의 같은 위치 값을 곱한 뒤 모두 더한다."""
    size = validate_matrix(pattern, name="패턴")
    validate_matrix(filter_matrix, expected_size=size, name="필터")

    score = 0.0

    for row in range(size):
        for column in range(size):
            score += pattern[row][column] * filter_matrix[row][column]

    return score


def decide_by_scores(score_a, score_b):
    """epsilon을 이용해 동점을 판정하고 더 높은 점수의 필터를 선택한다."""
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"

    return "A" if score_a > score_b else "B"


def decide_by_labeled_scores(cross_score, x_score):
    """Cross와 X 중 높은 점수를 선택한다."""
    if abs(cross_score - x_score) < EPSILON:
        return "UNDECIDED"

    return "Cross" if cross_score > x_score else "X"


def measure_average_time(pattern, filter_matrix, repeat_count=REPEAT_COUNT):
    """입출력 시간을 제외하고 MAC 함수 호출 시간의 평균을 ms로 반환한다."""
    # 측정 전 1회 실행(워밍업)
    mac_operation(pattern, filter_matrix)

    start = time.perf_counter()

    for _ in range(repeat_count):
        mac_operation(pattern, filter_matrix)

    elapsed = time.perf_counter() - start
    return (elapsed / repeat_count) * 1000


def create_pattern(size, label):
    """보너스 기능: 십자가 또는 X 패턴을 자동 생성한다."""
    normalized = normalize_label(label)
    matrix = []

    for row in range(size):
        values = []
        for column in range(size):
            if normalized == "Cross":
                # 중앙 행 또는 중앙 열을 1로 만든다.
                value = 1 if row == size // 2 or column == size // 2 else 0
            else:
                # 두 대각선을 1로 만든다.
                value = 1 if row == column or row + column == size - 1 else 0
            values.append(value)
        matrix.append(values)

    return matrix


# --------------------------------------------------
# 2. 사용자 입력 모드
# --------------------------------------------------

def input_matrix(size, title):
    """한 줄씩 입력받고 형식이 잘못되면 다시 입력받는다."""
    print(f"\n{title} ({size}줄 입력, 공백 구분)")

    while True:
        matrix = []
        try:
            for row_number in range(size):
                raw = input(f"{row_number + 1}행: ").strip()
                parts = raw.split()

                if len(parts) != size:
                    raise ValueError(
                        f"각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요."
                    )

                row = [float(value) for value in parts]
                matrix.append(row)

            validate_matrix(matrix, expected_size=size, name=title)
            return matrix

        except ValueError as error:
            print(f"입력 형식 오류: {error}")
            print("처음부터 다시 입력해 주세요.\n")


def print_matrix(matrix):
    for row in matrix:
        print(" ".join(f"{value:g}" for value in row))


def run_user_mode():
    print("\n" + "-" * 48)
    print("[1] 필터 입력")
    print("-" * 48)

    filter_a = input_matrix(3, "필터 A")
    filter_b = input_matrix(3, "필터 B")

    print("\n입력한 필터를 확인하세요.")
    print("필터 A:")
    print_matrix(filter_a)
    print("필터 B:")
    print_matrix(filter_b)

    print("\n" + "-" * 48)
    print("[2] 패턴 입력")
    print("-" * 48)

    pattern = input_matrix(3, "패턴")

    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    result = decide_by_scores(score_a, score_b)

    # 두 필터의 연산 시간을 각각 측정하고 평균을 표시한다.
    time_a = measure_average_time(pattern, filter_a)
    time_b = measure_average_time(pattern, filter_b)
    average_time = (time_a + time_b) / 2

    print("\n" + "-" * 48)
    print("[3] MAC 결과")
    print("-" * 48)
    print(f"A 점수: {score_a:.10f}")
    print(f"B 점수: {score_b:.10f}")
    print(f"연산 시간(평균/{REPEAT_COUNT}회): {average_time:.6f} ms")

    if result == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {result}")

    print("\n[성능 분석 - 3×3]")
    print(f"크기: 3×3 / 평균 시간: {average_time:.6f} ms / 연산 횟수: 9")


# --------------------------------------------------
# 3. JSON 로드 및 스키마 검증
# --------------------------------------------------

def load_json_file(file_path="data.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"{file_path} 파일을 찾을 수 없습니다. main.py와 같은 폴더에 두세요."
        )
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON 문법 오류: {error}")

    if not isinstance(data, dict):
        raise ValueError("JSON 최상위 구조는 객체(dict)여야 합니다.")

    if not isinstance(data.get("filters"), dict):
        raise ValueError("'filters' 항목이 없거나 객체가 아닙니다.")

    if not isinstance(data.get("patterns"), dict):
        raise ValueError("'patterns' 항목이 없거나 객체가 아닙니다.")

    return data


def load_filters(filters_data):
    """size_N 아래의 cross/x 필터를 표준 라벨 딕셔너리로 만든다."""
    loaded = {}

    for size_key, filter_group in filters_data.items():
        match = re.fullmatch(r"size_(\d+)", size_key)
        if not match:
            print(f"[경고] 알 수 없는 필터 키를 건너뜁니다: {size_key}")
            continue

        size = int(match.group(1))

        if not isinstance(filter_group, dict):
            print(f"[경고] {size_key}: 필터 묶음이 객체가 아닙니다.")
            continue

        normalized_group = {}

        for raw_label, matrix in filter_group.items():
            try:
                label = normalize_label(raw_label)
                validate_matrix(matrix, expected_size=size,
                                name=f"{size_key}.{raw_label}")
                normalized_group[label] = matrix
            except ValueError as error:
                print(f"[경고] 필터 로드 실패 - {size_key}.{raw_label}: {error}")

        loaded[size] = normalized_group

    return loaded


def extract_size_from_pattern_key(pattern_key):
    """size_5_1 같은 키에서 N=5를 추출한다."""
    match = re.fullmatch(r"size_(\d+)_\d+", pattern_key)
    if not match:
        raise ValueError(
            f"패턴 키 형식이 올바르지 않습니다: {pattern_key} "
            "(예: size_5_1)"
        )
    return int(match.group(1))


def analyze_one_case(pattern_key, case_data, loaded_filters):
    """패턴 하나를 분석하고 결과 또는 실패 사유를 반환한다."""
    try:
        if not isinstance(case_data, dict):
            raise ValueError("케이스 데이터가 객체(dict)가 아닙니다.")

        size = extract_size_from_pattern_key(pattern_key)

        if "input" not in case_data:
            raise ValueError("'input' 항목이 없습니다.")
        if "expected" not in case_data:
            raise ValueError("'expected' 항목이 없습니다.")

        pattern = case_data["input"]
        validate_matrix(pattern, expected_size=size, name="입력 패턴")
        expected = normalize_label(case_data["expected"])

        if size not in loaded_filters:
            raise ValueError(f"size_{size} 필터가 없습니다.")

        filter_group = loaded_filters[size]

        if "Cross" not in filter_group:
            raise ValueError(f"size_{size}의 Cross 필터가 없습니다.")
        if "X" not in filter_group:
            raise ValueError(f"size_{size}의 X 필터가 없습니다.")

        cross_score = mac_operation(pattern, filter_group["Cross"])
        x_score = mac_operation(pattern, filter_group["X"])
        prediction = decide_by_labeled_scores(cross_score, x_score)

        status = "PASS" if prediction == expected else "FAIL"

        reason = ""
        if status == "FAIL":
            if prediction == "UNDECIDED":
                reason = "동점(epsilon) 처리로 판정 불가"
            else:
                reason = f"예측 라벨({prediction})과 expected({expected}) 불일치"

        return {
            "case": pattern_key,
            "size": size,
            "cross_score": cross_score,
            "x_score": x_score,
            "prediction": prediction,
            "expected": expected,
            "status": status,
            "reason": reason
        }

    except (ValueError, TypeError, KeyError) as error:
        return {
            "case": pattern_key,
            "size": None,
            "status": "FAIL",
            "reason": str(error)
        }


def run_json_mode():
    print("\n" + "-" * 48)
    print("[1] 필터 및 패턴 데이터 로드")
    print("-" * 48)

    try:
        data = load_json_file()
    except (FileNotFoundError, ValueError) as error:
        print(f"데이터 로드 실패: {error}")
        return

    loaded_filters = load_filters(data["filters"])

    for size in SUPPORTED_SIZES[1:]:
        group = loaded_filters.get(size, {})
        if "Cross" in group and "X" in group:
            print(f"✓ size_{size} 필터 로드 완료 (Cross, X)")
        else:
            print(f"✗ size_{size} 필터가 완전하게 로드되지 않았습니다.")

    print("\n" + "-" * 48)
    print("[2] 패턴 분석 (라벨 정규화 적용)")
    print("-" * 48)

    results = []

    for pattern_key, case_data in data["patterns"].items():
        result = analyze_one_case(pattern_key, case_data, loaded_filters)
        results.append(result)

        print(f"\n--- {pattern_key} ---")

        if result.get("size") is not None and "cross_score" in result:
            print(f"Cross 점수: {result['cross_score']:.10f}")
            print(f"X 점수: {result['x_score']:.10f}")
            print(
                f"판정: {result['prediction']} | "
                f"expected: {result['expected']} | {result['status']}"
            )
            if result["reason"]:
                print(f"실패 사유: {result['reason']}")
        else:
            print(f"FAIL: {result['reason']}")

    print("\n" + "-" * 48)
    print(f"[3] 성능 분석 (평균/{REPEAT_COUNT}회)")
    print("-" * 48)
    print(f"{'크기':<12}{'평균 시간(ms)':<20}{'연산 횟수(N²)'}")
    print("-" * 48)

    # 각 크기의 실제 필터와 패턴이 있으면 해당 데이터로 측정한다.
    for size in SUPPORTED_SIZES:
        group = loaded_filters.get(size, {})
        if "Cross" in group:
            sample_filter = group["Cross"]
        else:
            sample_filter = create_pattern(size, "Cross")

        sample_pattern = None
        for result in results:
            if result.get("size") == size:
                case = data["patterns"][result["case"]]
                if isinstance(case, dict) and isinstance(case.get("input"), list):
                    try:
                        validate_matrix(case["input"], expected_size=size)
                        sample_pattern = case["input"]
                        break
                    except ValueError:
                        pass

        if sample_pattern is None:
            sample_pattern = create_pattern(size, "Cross")

        average_time = measure_average_time(
            sample_pattern, sample_filter, REPEAT_COUNT
        )
        print(f"{size}×{size:<9}{average_time:<20.6f}{size * size}")

    total = len(results)
    passed = sum(1 for result in results if result["status"] == "PASS")
    failed = total - passed

    print("\n" + "-" * 48)
    print("[4] 결과 요약")
    print("-" * 48)
    print(f"전체 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    if failed:
        print("\n실패 케이스:")
        for result in results:
            if result["status"] == "FAIL":
                print(f"- {result['case']}: {result['reason']}")
    else:
        print("\n모든 테스트가 통과했습니다.")


# --------------------------------------------------
# 4. 메인 실행
# --------------------------------------------------

def main():
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3×3)")
    print("2. data.json 분석")
    print("0. 종료")

    while True:
        choice = input("\n선택: ").strip()

        if choice == "1":
            run_user_mode()
            break
        elif choice == "2":
            run_json_mode()
            break
        elif choice == "0":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 1, 2, 0 중에서 입력하세요.")


if __name__ == "__main__":
    main()
