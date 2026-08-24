# **GATE EVIDENCE**
+ I purposely modified line 23 of backend/tests/test_api.py to have the test look for error code 300 instead of 200.
+ Doing this proved the github action failed, see full results here: https://github.com/mikerukaj/saras_ai_10x-engineer-project-repo/actions/runs/32696502291/job/97339473833#step:5:78
+ Error log output below also.


> ============================= test session starts ==============================  
> platform linux -- Python 3.12.14, pytest-7.4.4, pluggy-1.6.0  
> rootdir: /home/runner/work/saras_ai_10x-engineer-project-repo/saras_ai_10x-engineer-project-repo/backend
> plugins: anyio-4.14.2, cov-4.1.0
> collected 471 items
>  
> tests/test_api.py F..............[ 26%]    
> tests/test_models.py ........... [ 30%]  
> tests/test_prompt_version.py ... [ 38%]  
> tests/test_storage.py .......... [ 73%]  
> tests/test_utils.py ............ [100%]  
>  
> =================================== FAILURES ===================================  
> ___________________ TestHealth.test_health_check_returns_200 ___________________  
>  
> self = <tests.test_api.TestHealth object at 0x7f64a7c1dbe0>  
> client = <starlette.testclient.TestClient object at 0x7f64a7c73110>  
> 
>     def test_health_check_returns_200(self, client: TestClient):  
>         """GET /health must respond 200 OK per the documented contract  
>         (docs/API_REFERENCE.md, specs/.../contracts/api-contract.md)."""  
>         response = client.get("/health")  
>       assert response.status_code == 300  
> E       assert 200 == 300  
> E        +  where 200 = <Response [200 OK]>.status_code  
> 
> tests/test_api.py:23: AssertionError  
> =============================== warnings summary ===============================  
> ../../../../../../opt/hostedtoolcache/Python/3.12.14/x64/lib/python3.12/site-packages/pydantic/_internal/_config.py:271  
> ../../../../../../opt/hostedtoolcache/Python/3.12.14/x64/lib/python3.12/site-packages/pydantic/_internal/_config.py:271  
>   /opt/hostedtoolcache/Python/3.12.14/x64/lib/python3.12/site-packages/pydantic/_internal/_config.py:271: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.5/migration/  
>     warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)  
> 
>  tests/test_api.py: 368 warnings
>  tests/test_models.py: 208 warnings
>  tests/test_prompt_version.py: 151 warnings
>  tests/test_storage.py: 491 warnings
>  tests/test_utils.py: 191 warnings
>    /home/runner/work/saras_ai_10x-engineer-project-repo/saras_ai_10x-engineer-project-repo/backend/app/models.py:35: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).  
>     return datetime.utcnow()
> 
> -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html  
> 
> ---------- coverage: platform linux, python 3.12.14-final-0 ----------  
> 
> | Name | Stmts | Miss | Cover | Missing|
> | --- | --- | --- | ---| --- |
> | app/__init__.py | 1 | 0 | 100% | |
> | app/api.py| 142| 0 | 100% | |
> | app/models.py | 61 | 0 | 100% | |
> | app/storage.py | 60 | 1 | 98% | 332 | |
> | app/utils.py | 17  | 0 | 100% | |
> | TOTAL | 281 | 1 | 99% | |  
> Coverage XML written to file coverage.xml
> 
> Required test coverage of 80% reached. Total coverage: 99.64%  
> =========================== short test summary info ============================  
> FAILED tests/test_api.py::TestHealth::test_health_check_returns_200 - assert 200 == 300  
>  \+  where 200 = <Response [200 OK]>.status_code  
> ================= 1 failed, 470 passed, 1411 warnings in 4.19s =================  
> Error: Process completed with exit code 1.

