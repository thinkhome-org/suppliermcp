import pytest
from suppliermcp.catalog.contracts import Filter, CatalogError
from suppliermcp.search.schema import validate_filter


def test_invalid_filter_and_type():
    schema={'capacity':{'type':'number','operators':['eq','gte','lte']}}
    assert validate_filter(Filter(field='capacity',operator='gte',value=32),schema).value==32
    for f in [Filter(field='unknown',operator='eq',value='x'),Filter(field='capacity',operator='gte',value='not a number')]:
        with pytest.raises(CatalogError): validate_filter(f,schema)
