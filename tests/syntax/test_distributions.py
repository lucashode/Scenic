
import pytest
import math
import random

from scenic.core.errors import RuntimeParseError, InvalidScenarioError, ScenicSyntaxError
from tests.utils import compileScenic, sampleScene, sampleEgo, sampleEgoFrom, sampleParamP

## Utilities

def lazyTestScenario(expr, offset='0'):
    """Scenario for testing a lazily-evaluated value inside a distribution.

    Here the value 'x' lazily evaluates to 1 (plus the offset, if any).
    """
    return compileScenic(f"""
        vf = VectorField("Foo", lambda pos: 2 * pos.x)
        x = {offset} relative to vf
        ego = Object at 0.5 @ 0, facing {expr}
    """)

## Range and DiscreteRange

def test_range():
    scenario = compileScenic('ego = Object at Range(3, 5) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(60)]
    assert all(3 <= x <= 5 for x in xs)
    assert any(x < 4 for x in xs)
    assert any(x > 4 for x in xs)

def test_range_lazy():
    scenario = lazyTestScenario('Range(0, x)')
    xs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(0 <= x <= 1 for x in xs)
    assert any(x < 0.5 for x in xs)
    assert any(x > 0.5 for x in xs)

def test_range_random_endpoint():
    scenario = compileScenic('ego = Object at Range(0, Uniform(1, 10000)) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(60)]
    assert all(0 <= x <= 10000 for x in xs)
    assert 5 <= sum(x > 1 for x in xs) <= 55

def test_discrete_range():
    scenario = compileScenic('ego = Object at DiscreteRange(-1, 1) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(100)]
    assert all(x == -1 or x == 0 or x == 1 for x in xs)
    assert any(x == -1 for x in xs)
    assert any(x == 0 for x in xs)
    assert any(x == 1 for x in xs)

def test_discrete_range_errors():
    with pytest.raises(ValueError):
        compileScenic('ego = Object at DiscreteRange(Range(0, 1), 2) @ 0')
    with pytest.raises(ValueError):
        compileScenic('ego = Object at DiscreteRange(2, Range(0, 1)) @ 0')
    with pytest.raises(ValueError):
        compileScenic('ego = Object at DiscreteRange(2, 1) @ 0')

## Normal and TruncatedNormal

def test_normal():
    scenario = compileScenic('ego = Object at Normal(100, 2) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(60)]
    assert all(80 <= x <= 120 for x in xs)
    assert any(x < 100 for x in xs)
    assert any(x > 100 for x in xs)
    assert sum(98 <= x <= 102 for x in xs) >= 9
    assert sum(96 <= x <= 104 for x in xs) >= 30

def test_normal_lazy():
    scenario = lazyTestScenario('Normal(-5, x)')
    xs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(-15 <= x <= 5 for x in xs)
    assert any(x < -5 for x in xs)
    assert any(x > -5 for x in xs)

def test_truncated_normal():
    scenario = compileScenic('ego = Object at TruncatedNormal(100, 2, 99, 110) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(60)]
    assert all(99 <= x <= 110 for x in xs)
    assert any(x < 101 for x in xs)
    assert any(x > 101 for x in xs)

def test_truncated_normal_lazy():
    scenario = lazyTestScenario('TruncatedNormal(100, 1+x, 96, 99)')
    xs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(96 <= x <= 99 for x in xs)
    assert any(x < 98 for x in xs)
    assert any(x > 98 for x in xs)

def test_truncated_normal_errors():
    with pytest.raises(ValueError):
        compileScenic('ego = Object at TruncatedNormal(0, 2, 5, Range(6, 9))')
    with pytest.raises(ValueError):
        compileScenic('ego = Object at TruncatedNormal(0, 2, 5, 3)')

## Options and Uniform

def test_options_empty_domain():
    with pytest.raises(InvalidScenarioError):
        compileScenic('x = Options([])')
    with pytest.raises(InvalidScenarioError):
        compileScenic('x = Options({})')
    with pytest.raises(InvalidScenarioError):
        compileScenic('x = Uniform()')
    with pytest.raises(InvalidScenarioError):
        compileScenic('x = Discrete({})')

def test_options_invalid_weight():
    with pytest.raises(RuntimeParseError):
        compileScenic('x = Options({0: 1, 1: -2})')
    with pytest.raises(RuntimeParseError):
        compileScenic('x = Options({0: 1, 1: []})')
    with pytest.raises(RuntimeParseError):
        compileScenic('x = Options({0: 1, 1: Range(3, 5)})')

def test_uniform_interval_wrong_type():
    with pytest.raises(RuntimeParseError):
        compileScenic('x = Range([], 4)')
    with pytest.raises(RuntimeParseError):
        compileScenic('x = Range(-10, [])')

def test_uniform_discrete():
    scenario = compileScenic('ego = Object at Uniform(1, 2, 3.4) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(100)]
    assert all(x == 1 or x == 2 or x == 3.4 for x in xs)
    assert any(x == 1 for x in xs)
    assert any(x == 2 for x in xs)
    assert any(x == 3.4 for x in xs)

def test_uniform_discrete_lazy():
    scenario = lazyTestScenario('Uniform(1.2, x)')
    hs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(h == 1.2 or h == pytest.approx(1) for h in hs)
    assert any(h == 1.2 for h in hs)
    assert any(h == pytest.approx(1) for h in hs)

@pytest.mark.parametrize('dist', ('Options', 'Discrete'))
def test_options(dist):
    scenario = compileScenic(f'ego = Object at {dist}({{0: 1, 1: 9}}) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(200)]
    assert all(x == 0 or x == 1 for x in xs)
    assert 145 <= sum(xs) < 200

def test_options_lazy():
    scenario = lazyTestScenario('Options({0: 1, x: 9})')
    hs = [sampleEgo(scenario).heading for i in range(200)]
    assert all(h == 0 or h == pytest.approx(1) for h in hs)
    assert 145 <= sum(hs) < 200

## Functions, methods, attributes, operators

def test_function():
    scenario = compileScenic('ego = Object at sin(Uniform(45 deg, 90 deg)) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(60)]
    valA, valB = (pytest.approx(math.sin(math.radians(a))) for a in (45, 90))
    assert all(x == valA or x == valB for x in xs)
    assert any(x == valA for x in xs)
    assert any(x == valB for x in xs)

def test_function_lazy():
    scenario = lazyTestScenario('hypot(Uniform(5, 35), 12 * x)')
    hs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(h == pytest.approx(13) or h == pytest.approx(37) for h in hs)
    assert any(h == pytest.approx(13) for h in hs)
    assert any(h == pytest.approx(37) for h in hs)

def test_function_lazy_2():
    scenario = lazyTestScenario('sin(x * 90 deg)', offset='Uniform(-1, 0)')
    hs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(h == pytest.approx(0) or h == pytest.approx(1) for h in hs)
    assert any(h == pytest.approx(0) for h in hs)
    assert any(h == pytest.approx(1) for h in hs)

def test_method():
    scenario = compileScenic("""
        field = VectorField("Foo", lambda pos: pos[1])
        ang = field[0 @ Range(100, 200)]
        ego = Object facing ang
    """)
    angles = [sampleEgo(scenario).heading for i in range(60)]
    assert all(100 <= x <= 200 for x in angles)
    assert any(x < 150 for x in angles)
    assert any(150 < x for x in angles)

def test_method_lazy():
    scenario = compileScenic("""
        from scenic.core.distributions import distributionMethod
        class Foo(object):
            @distributionMethod
            def bar(self, arg):
                return -arg
        vf = VectorField("Baz", lambda pos: 1 + pos.x)
        ego = Object facing Foo().bar(Range(100, 200) * (0 relative to vf))
    """)
    angles = [sampleEgo(scenario).heading for i in range(60)]
    assert all(-200 <= x <= -100 for x in angles)
    assert any(x < -150 for x in angles)
    assert any(-150 < x for x in angles)

def test_method_lazy_2():
    scenario = compileScenic("""
        from scenic.core.distributions import distributionMethod
        class Foo(object):
            @distributionMethod
            def bar(self, arg):
                return -arg * Range(100, 200)
        vf = VectorField("Baz", lambda pos: 1 + pos.x)
        ego = Object facing Foo().bar(0 relative to vf)
    """)
    angles = [sampleEgo(scenario).heading for i in range(60)]
    assert all(-200 <= x <= -100 for x in angles)
    assert any(x < -150 for x in angles)
    assert any(-150 < x for x in angles)

def test_method_lazy_3():
    scenario = compileScenic("""
        reg = PolylineRegion([0@0, 2@0])
        vf = VectorField('Foo', lambda pos: 1 + pos.x)
        ego = Object with foo reg.distanceTo(1 @ (Range(2, 4) relative to vf))
    """)
    fs = [sampleEgo(scenario).foo for i in range(60)]
    assert all(3 <= f <= 5 for f in fs)
    assert any(f < 4 for f in fs)
    assert any(4 < f for f in fs)

def test_method_starred():
    scenario = compileScenic("""
        from scenic.core.distributions import distributionMethod
        class Foo(object):
            @distributionMethod
            def bar(self, *args):
                return sum(args)
        vs = Uniform([5], [-2, -3])
        ego = Object with baz Foo().bar(Range(0, 1), *vs)
    """)
    bs = [sampleEgo(scenario).baz for i in range(60)]
    assert all(5 <= b <= 6 or -5 <= b <= -4 for b in bs)
    assert any(5 <= b <= 6 for b in bs)
    assert any(-5 <= b <= -4 for b in bs)

def test_attribute():
    scenario = compileScenic("""
        place = Uniform(1 @ 1, 2 @ 4, 3 @ 9)
        ego = Object at place.x @ place.y
    """)
    xs = [sampleEgo(scenario).position.x for i in range(100)]
    assert all(x == 1 or x == 2 or x == 3 for x in xs)
    assert any(x == 1 for x in xs)
    assert any(x == 2 for x in xs)
    assert any(x == 3 for x in xs)

def test_operator():
    scenario = compileScenic('ego = Object at -(100 + Range(0, 100)) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(60)]
    assert all(-200 <= x <= -100 for x in xs)
    assert any(x < -150 for x in xs)
    assert any(-150 < x for x in xs)

def test_operator_lazy():
    scenario = lazyTestScenario('Uniform(0, 1) * x')
    hs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(h == pytest.approx(0) or h == pytest.approx(1) for h in hs)
    assert any(h == pytest.approx(0) for h in hs)
    assert any(h == pytest.approx(1) for h in hs)

def test_callable():
    scenario = compileScenic('ego = Object at 0 @ Uniform(sin, cos)(0)')
    ys = [sampleEgo(scenario).position.y for i in range(60)]
    assert all(y == 0 or y == 1 for y in ys)
    assert any(y == 0 for y in ys)
    assert any(y == 1 for y in ys)

## Vectors

def test_vector_operator():
    scenario = compileScenic('ego = Object at Range(-3, 3) @ 0 + Range(100, 110) @ 0')
    xs = [sampleEgo(scenario).position.x for i in range(100)]
    assert all(97 <= x <= 113 for x in xs)
    assert any(x < 105 for x in xs)
    assert any(105 < x for x in xs)

def test_vector_method_lazy():
    scenario = lazyTestScenario('vf.followFrom(Uniform(0, 90 deg) @ 0, x, steps=1).y')
    hs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(h == pytest.approx(1) or h == pytest.approx(-1) for h in hs)
    assert any(h == pytest.approx(1) for h in hs)
    assert any(h == pytest.approx(-1) for h in hs)

def test_vector_method_lazy_2():
    scenario = lazyTestScenario('vf.followFrom(90 deg @ 0, x, steps=1).y')
    h = sampleEgo(scenario).heading
    assert h == pytest.approx(-1)

## Lists, tuples, namedtuples

def test_list():
    scenario = compileScenic('ego = Object with foo [3, Uniform(1, 2)]')
    ts = [sampleEgo(scenario).foo for i in range(60)]
    assert all(type(t) is list for t in ts)
    assert all(t[0] == 3 for t in ts)
    assert all(t[1] == 1 or t[1] == 2 for t in ts)
    assert any(t[1] == 1 for t in ts)
    assert any(t[1] == 2 for t in ts)

def test_list_param():
    scenario = compileScenic("""
        ego = Object
        param p = [3, Uniform(1, 2)]
    """)
    ts = [sampleParamP(scenario) for i in range(60)]
    assert all(type(t) is list for t in ts)
    assert all(t[0] == 3 for t in ts)
    assert all(t[1] == 1 or t[1] == 2 for t in ts)
    assert any(t[1] == 1 for t in ts)
    assert any(t[1] == 2 for t in ts)

def test_list_param_lazy():
    with pytest.raises(InvalidScenarioError):
        compileScenic("""
            vf = VectorField("Foo", lambda pos: 2 * pos.x)
            x = 0 relative to vf
            param p = Uniform([0, x], [0, x*2])[1]
            ego = Object
        """)

def test_list_object_lazy():
    scenario = lazyTestScenario('Uniform([0, x], [1, x])[1]', offset='Uniform(0, 1)')
    hs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(h == pytest.approx(1) or h == pytest.approx(2) for h in hs)
    assert any(h == pytest.approx(1) for h in hs)
    assert any(h == pytest.approx(2) for h in hs)

def test_list_nested():
    scenario = compileScenic("""
        mylist = Uniform(list(range(1000)), [1000])
        ego = Object with foo Uniform(*mylist)
    """)
    vs = [sampleEgo(scenario).foo for i in range(60)]
    assert 5 <= sum((v == 1000) for v in vs) <= 55

def test_list_nested_argument():
    scenario = compileScenic("""
        mylist = Uniform(list(range(1000)), [1, 1, 1, 1, 2000])
        ego = Object with foo max(*mylist)
    """)
    vs = [sampleEgo(scenario).foo for i in range(60)]
    assert 5 <= sum((v == 2000) for v in vs) <= 55

def test_list_filtered():
    scenario = compileScenic("""
        mylist = [Range(-10, -5), Range(3, 7), Range(-1, 1)]
        filtered = filter(lambda x: x > 0, mylist)
        ego = Object with foo Uniform(*filtered)
    """)
    vs = [sampleEgo(scenario).foo for i in range(60)]
    assert all(v > 0 for v in vs)
    assert any(v < 1 for v in vs)

def test_list_filtered_lazy():
    scenario = lazyTestScenario('Uniform(*filter(lambda x: x > 0, [-1, x, 3]))')
    hs = [sampleEgo(scenario).heading for i in range(60)]
    assert all(h == 1 or h == 3 for h in hs)
    assert any(h == 1 for h in hs)
    assert any(h == 3 for h in hs)

def test_list_filtered_empty_1():
    scenario = compileScenic("""
        mylist = [Range(-10, -5), Range(-3, 1)]
        filtered = filter(lambda x: x > 0, mylist)
        ego = Object with foo Uniform(*filtered)
    """)
    vs = [sampleEgo(scenario, maxIterations=100).foo for i in range(60)]
    assert all(0 <= v <= 1 for v in vs)
    assert any(v > 0.5 for v in vs)
    assert sum(v < 0.5 for v in vs)

def test_list_filtered_empty_2():
    scenario = compileScenic("""
        mylist = [Range(-10, -5), Range(-3, 1)]
        filtered = filter(lambda x: x > 0, mylist)
        ego = Object with foo Uniform(*filtered, 2)
    """)
    vs = [sampleEgo(scenario).foo for i in range(150)]
    assert all(0 <= v <= 1 or v == 2 for v in vs)
    assert any(0 <= v <= 1 for v in vs)
    assert sum(v == 2 for v in vs) >= 85

def test_tuple():
    scenario = compileScenic('ego = Object with foo tuple([3, Uniform(1, 2)])')
    ts = [sampleEgo(scenario).foo for i in range(60)]
    assert all(type(t) is tuple for t in ts)
    assert all(t[0] == 3 for t in ts)
    assert all(t[1] == 1 or t[1] == 2 for t in ts)
    assert any(t[1] == 1 for t in ts)
    assert any(t[1] == 2 for t in ts)

def test_tuple_iteration():
    ego = sampleEgoFrom("""
        other = Object with foo (1, Uniform(2, 3))
        data = [len(other.foo), other.foo[1], other.foo[0]]
        for item in other.foo:
            data.append(item)
        ego = Object at 2@2, with foo data
        require other.foo[1] == 3
    """, maxIterations=60)
    assert type(ego.foo) is list
    assert ego.foo == [2, 3, 1, 1, 3]

def test_tuple_param():
    scenario = compileScenic("""
        ego = Object
        param p = tuple([3, Uniform(1, 2)])
    """)
    ts = [sampleParamP(scenario) for i in range(60)]
    assert all(type(t) is tuple for t in ts)
    assert all(t[0] == 3 for t in ts)
    assert all(t[1] == 1 or t[1] == 2 for t in ts)
    assert any(t[1] == 1 for t in ts)
    assert any(t[1] == 2 for t in ts)

def test_namedtuple():
    scenario = compileScenic("""
        from collections import namedtuple
        Data = namedtuple("Data", ["bar", "baz"])
        ego = Object with foo Data(bar=3, baz=Uniform(1, 2))
    """)
    ts = [sampleEgo(scenario).foo for i in range(60)]
    assert all(t.bar == 3 for t in ts)
    assert all(t.baz == 1 or t.baz == 2 for t in ts)
    assert any(t.baz == 1 for t in ts)
    assert any(t.baz == 2 for t in ts)

## Comparisons and control flow

def test_comparison():
    with pytest.raises(RuntimeParseError):
        compileScenic('ego = Object with foo (Range(0, 1) > 0.5)')

def test_len():
    with pytest.raises(RuntimeParseError):
        compileScenic('ego = Object with foo len(Uniform([0], [1, 2]))')

def test_iter():
    with pytest.raises(RuntimeParseError):
        compileScenic("""
            for x in Uniform([1, 2], [3, 4]):
                ego = Object at x@0
        """)

def test_control_flow():
    with pytest.raises(RuntimeParseError):
        compileScenic("""
            if Uniform(False, True):
                ego = Object
            else:
                ego = Object at 1@1
        """)

## Reproducibility

@pytest.mark.slow
def test_reproducibility():
    scenario = compileScenic("""
        ego = Object
        Object offset by 0@3, facing Range(0, 360) deg
        Object offset by 0@6, facing Range(0, 360) deg
        param foo = Uniform(1, 4, 9, 16, 25, 36)
        x = Range(0, 1)
        require x > 0.8
    """)
    seeds = [random.randint(0, 100000) for i in range(10)]
    for seed in seeds:
        random.seed(seed)
        baseScene, baseIterations = scenario.generate(maxIterations=200)
        for j in range(20):
            random.seed(seed)
            scene, iterations = scenario.generate(maxIterations=200)
            assert len(scene.objects) == len(baseScene.objects)
            for obj, baseObj in zip(scene.objects, baseScene.objects):
                assert obj.heading == baseObj.heading
            assert scene.params['foo'] == baseScene.params['foo']
            assert iterations == baseIterations

## Independence and resampling

def test_independence():
    scenario = compileScenic('ego = Object at Range(0, 1) @ Range(0, 1)')
    pos = sampleEgo(scenario).position
    assert pos.x != pos.y

def test_resample():
    scenario = compileScenic("""
        x = Range(0, 1)
        ego = Object at x @ resample(x)
    """)
    pos = sampleEgo(scenario).position
    assert pos.x != pos.y

def test_resample_complex():
    with pytest.raises(ScenicSyntaxError):
        compileScenic('ego = Object at 0 @ resample(Range(0,1) + Range(1,2))')

## Dependencies and lazy evaluation

def test_shared_dependency():
    scenario = compileScenic("""
        x = Range(-1, 1)
        ego = Object at (x * x) @ 0
    """)
    xs = [sampleEgo(scenario).position.x for i in range(60)]
    assert all(0 <= x <= 1 for x in xs)
    assert any(x < 0.25 for x in xs)
    assert any(0.25 < x for x in xs)

def test_shared_dependency_lazy_1():
    scenario = compileScenic("""
        vf = VectorField("Foo", lambda pos: 2 * pos.x)
        x = 1 relative to vf
        y = Uniform(0, x)
        ego = Object with foo y, with bar y
    """)
    for i in range(60):
        ego = sampleEgo(scenario)
        assert ego.foo == 0 or ego.foo == 1
        assert ego.foo == ego.bar

def test_shared_dependency_lazy_2():
    scenario = compileScenic("""
        vf = VectorField("Foo", lambda pos: 2 * pos.x)
        x = Range(0, 1) relative to vf
        ego = Object at 1 @ 0, facing x
        other = Object at -1 @ 0, facing x
    """)
    for i in range(60):
        scene = sampleScene(scenario, maxIterations=1)
        egoH = scene.objects[0].heading
        assert 2 <= egoH <= 3
        otherH = scene.objects[1].heading
        assert -2 <= otherH <= -1
        assert (egoH - otherH) == pytest.approx(4)

def test_inside_delayed_argument():
    scenario = lazyTestScenario('Uniform(1.2, x)', offset='Uniform(-1, 1)')
    hs = [sampleEgo(scenario).heading for i in range(140)]
    assert all(h == 1.2 or h == pytest.approx(0) or h == pytest.approx(2) for h in hs)
    assert any(h == 1.2 for h in hs)
    assert any(h == pytest.approx(0) for h in hs)
    assert any(h == pytest.approx(2) for h in hs)

## Typechecking

def test_object_expression():
    scenario = compileScenic("""
        v = Uniform((Object at Range(-2,-1) @ 0), Object at Range(1,2) @ 5).position.x
        ego = Object facing v, at 0 @ 10
        require abs(v) > 1.5
    """)
    for i in range(3):
        scene = sampleScene(scenario, maxIterations=50)
        assert len(scene.objects) == 3
