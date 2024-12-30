class OpenDartApiError(Exception):
    """OpenDart API 호출 중 발생한 오류를 나타냅니다."""
    pass

class CorpCodeFetchError(Exception):
    """고유번호(corp_code) 조회 중 발생한 오류를 나타냅니다."""
    pass

class DividendScreeningError(Exception):
    """배당 스크리닝 중 발생한 오류를 나타냅니다."""
    pass

class NoPriceDataError(Exception):
    """주가 데이터를 가져올 수 없을 때 발생하는 오류를 나타냅니다."""
    pass

class APIError(Exception):
    """일반적인 API 오류를 나타냅니다."""
    pass

class RateLimitError(Exception):
    """API 요청 제한에 도달했을 때 발생하는 오류를 나타냅니다."""
    pass