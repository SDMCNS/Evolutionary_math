"""Grounded Physical & Geometric Seeds (Environmental Framework for Evolutionary Math).

Provides tangible starting environments with observable physical features:
- Edges, side lengths, and collinear segments
- Angles and interior vertices
- Parallel lines and perpendicular (orthogonal) intersections
- Heights, diagonals, perimeters, and surface areas

The evolutionary population operates in these grounded environments, experimenting
with observable raw materials to discover predictable laws and geometric invariants.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from evolutionary_math.core.ast import ExprNode, parse_expr_str


@dataclass
class DiscoveryGoal:
    """A predictable aspect or invariant to discover from observable features."""
    name: str
    predicted_feature: str
    target_expr_str: str
    target_ast: ExprNode
    mathematical_meaning: str
    observable_clues: str


@dataclass
class GeometricSeed:
    """An observable geometric shape environment with physical features and constraints."""
    id: str
    name: str
    dimension: int  # e.g. 2 for 2D plane geometry, 3 for 3D solid geometry
    description: str
    observable_features: Dict[str, str]  # Feature symbol -> Physical description
    geometric_properties: List[str]     # Observable constraints (e.g. parallel, perpendicular)
    primary_variables: List[str]
    goals: List[DiscoveryGoal] = field(default_factory=list)

    def get_goal(self, feature_or_name: str) -> Optional[DiscoveryGoal]:
        """Lookup a discovery goal by feature name or target name."""
        clean = feature_or_name.lower().strip()
        for g in self.goals:
            if g.predicted_feature.lower() == clean or g.name.lower() == clean:
                return g
        for g in self.goals:
            if clean in g.predicted_feature.lower() or clean in g.name.lower():
                return g
        return None

    def get_targets(self) -> List[ExprNode]:
        """Return the sequence of discovery target ASTs for this seed."""
        return [g.target_ast for g in self.goals]


# Built-in Shape Seeds
SEEDS: Dict[str, GeometricSeed] = {}


def _create_default_seeds() -> Dict[str, GeometricSeed]:
    seeds = {}

    # 1. Rectangle Seed
    rect_goals = [
        DiscoveryGoal(
            name="Rectangle Perimeter",
            predicted_feature="P",
            target_expr_str="2 * (a + b)",
            target_ast=parse_expr_str("2 * (a + b)"),
            mathematical_meaning="Total boundary length summing all four perimeter edges: 2a + 2b = 2(a + b).",
            observable_clues="Opposite edges are equal (a, a and b, b); path around boundary traverses each twice.",
        ),
        DiscoveryGoal(
            name="Rectangle Area",
            predicted_feature="A",
            target_expr_str="a * b",
            target_ast=parse_expr_str("a * b"),
            mathematical_meaning="Interior 2D surface tile count: base length multiplied by orthogonal height.",
            observable_clues="Edges meet at 90° perpendicular corners, creating an a × b grid of unit tiles.",
        ),
        DiscoveryGoal(
            name="Rectangle Diagonal",
            predicted_feature="d",
            target_expr_str="sqrt(a^2 + b^2)",
            target_ast=parse_expr_str("sqrt(a^2 + b^2)"),
            mathematical_meaning="Straight corner-to-corner internal span connecting opposite vertices.",
            observable_clues="Perpendicular adjacent edges form right-angle corner spanning the diagonal.",
        ),
        DiscoveryGoal(
            name="Rectangle Semi-Perimeter",
            predicted_feature="s",
            target_expr_str="a + b",
            target_ast=parse_expr_str("a + b"),
            mathematical_meaning="Half-boundary length encompassing one adjacent width and height.",
            observable_clues="Traversing one horizontal edge and one vertical edge.",
        ),
    ]
    seeds["rectangle"] = GeometricSeed(
        id="rectangle",
        name="Rectangle",
        dimension=2,
        description="2D quadrilateral with 4 perpendicular vertices (90°) and 2 pairs of parallel opposite sides.",
        observable_features={
            "a": "Width / horizontal edge length",
            "b": "Height / vertical edge length",
            "P": "Perimeter (total boundary distance)",
            "A": "Area (interior surface measure)",
            "d": "Diagonal (corner-to-corner span)",
        },
        geometric_properties=[
            "Opposite sides are parallel (a ∥ a, b ∥ b)",
            "Adjacent edges are perpendicular (a ⟂ b, four 90° angles)",
            "Diagonals are equal in length and bisect each other",
        ],
        primary_variables=["a", "b"],
        goals=rect_goals,
    )

    # 2. Right Triangle Seed
    rt_goals = [
        DiscoveryGoal(
            name="Pythagorean Hypotenuse",
            predicted_feature="c",
            target_expr_str="sqrt(a^2 + b^2)",
            target_ast=parse_expr_str("sqrt(a^2 + b^2)"),
            mathematical_meaning="Length of the longest edge opposite the perpendicular 90° right angle.",
            observable_clues="The two legs a and b are perpendicular; squaring their spans predicts the hypotenuse.",
        ),
        DiscoveryGoal(
            name="Right Triangle Area",
            predicted_feature="A",
            target_expr_str="(a * b) / 2",
            target_ast=parse_expr_str("(a * b) / 2"),
            mathematical_meaning="Interior 2D area, exactly half of the bounding rectangle formed by perpendicular legs.",
            observable_clues="Bisecting an a × b rectangle along its diagonal creates two identical right triangles.",
        ),
        DiscoveryGoal(
            name="Pythagorean Sum of Squares",
            predicted_feature="c^2",
            target_expr_str="a^2 + b^2",
            target_ast=parse_expr_str("a^2 + b^2"),
            mathematical_meaning="Fundamental quadratic invariant of perpendicular line segments: a² + b² = c².",
            observable_clues="Geometric square tiles built on legs a and b perfectly tile the square built on hypotenuse c.",
        ),
    ]
    seeds["right_triangle"] = GeometricSeed(
        id="right_triangle",
        name="Right Triangle",
        dimension=2,
        description="2D triangle featuring one perpendicular intersection (90° right angle) between orthogonal legs.",
        observable_features={
            "a": "Base leg length",
            "b": "Perpendicular altitude / leg length",
            "c": "Hypotenuse (longest edge opposite right angle)",
            "A": "Interior area",
        },
        geometric_properties=[
            "One pair of perpendicular edges (a ⟂ b)",
            "Interior angle sum equals 180° (alpha + beta + 90° = 180°)",
            "Hypotenuse is always strictly greater than either leg (c > a, c > b)",
        ],
        primary_variables=["a", "b"],
        goals=rt_goals,
    )

    # 3. General Triangle Seed
    tri_goals = [
        DiscoveryGoal(
            name="Triangle Perimeter",
            predicted_feature="P",
            target_expr_str="a + b + c",
            target_ast=parse_expr_str("a + b + c"),
            mathematical_meaning="Total boundary perimeter summing all three side lengths: a + b + c.",
            observable_clues="Path visiting all three vertices around the closed 2D polygon.",
        ),
        DiscoveryGoal(
            name="Triangle Semi-Perimeter",
            predicted_feature="s",
            target_expr_str="(a + b + c) / 2",
            target_ast=parse_expr_str("(a + b + c) / 2"),
            mathematical_meaning="Half-perimeter used in Heron's formula and circumradius calculations.",
            observable_clues="Total boundary sum divided by 2.",
        ),
        DiscoveryGoal(
            name="Triangle Area (Base & Height)",
            predicted_feature="A",
            target_expr_str="(a * h) / 2",
            target_ast=parse_expr_str("(a * h) / 2"),
            mathematical_meaning="Interior area given base length and perpendicular altitude: (base × height) / 2.",
            observable_clues="Any triangle can be sheared into half of an a × h parallelogram.",
        ),
    ]
    seeds["general_triangle"] = GeometricSeed(
        id="general_triangle",
        name="General Triangle",
        dimension=2,
        description="Arbitrary 2D 3-sided polygon with 3 vertices, side lengths a, b, c, and altitude h.",
        observable_features={
            "a": "Base edge length",
            "b": "Second edge length",
            "c": "Third edge length",
            "h": "Perpendicular altitude to base a",
            "P": "Perimeter",
            "A": "Area",
        },
        geometric_properties=[
            "Triangle inequality: sum of any two sides strictly exceeds third (a + b > c)",
            "Interior angle sum is an invariant 180° across all configurations",
            "Altitude h drops perpendicularly to the base line (h ⟂ a)",
        ],
        primary_variables=["a", "b", "c"],
        goals=tri_goals,
    )

    # 4. Trapezoid Seed
    trap_goals = [
        DiscoveryGoal(
            name="Trapezoid Area",
            predicted_feature="A",
            target_expr_str="((a + b) * h) / 2",
            target_ast=parse_expr_str("((a + b) * h) / 2"),
            mathematical_meaning="Area determined by average length of parallel bases multiplied by height.",
            observable_clues="Two parallel lines a and b separated by orthogonal distance h; average width is (a+b)/2.",
        ),
        DiscoveryGoal(
            name="Trapezoid Median (Mid-Segment)",
            predicted_feature="m",
            target_expr_str="(a + b) / 2",
            target_ast=parse_expr_str("(a + b) / 2"),
            mathematical_meaning="Length of the segment connecting the midpoints of the non-parallel legs.",
            observable_clues="Arithmetic mean of the two parallel bases.",
        ),
    ]
    seeds["trapezoid"] = GeometricSeed(
        id="trapezoid",
        name="Trapezoid",
        dimension=2,
        description="2D quadrilateral possessing exactly one pair of parallel opposite edges (bases a and b).",
        observable_features={
            "a": "Top parallel base length",
            "b": "Bottom parallel base length",
            "h": "Orthogonal perpendicular distance between bases",
            "A": "Area",
            "m": "Mid-segment length",
        },
        geometric_properties=[
            "Exactly one pair of parallel edges (a ∥ b)",
            "Height h is perpendicular to both parallel bases (h ⟂ a, h ⟂ b)",
            "Interior angle pairs between parallel lines sum to 180°",
        ],
        primary_variables=["a", "b", "h"],
        goals=trap_goals,
    )

    # 5. Circle Seed
    circ_goals = [
        DiscoveryGoal(
            name="Circle Diameter",
            predicted_feature="d",
            target_expr_str="2 * r",
            target_ast=parse_expr_str("2 * r"),
            mathematical_meaning="Maximum internal distance across center connecting opposite boundary points.",
            observable_clues="Composed of two collinear radial segments meeting at the center: r + r.",
        ),
        DiscoveryGoal(
            name="Circle Area Scale",
            predicted_feature="A_proxy",
            target_expr_str="r^2",
            target_ast=parse_expr_str("r^2"),
            mathematical_meaning="Quadratic growth law of circular surface area proportional to radius squared.",
            observable_clues="Area scales quadratically with 2D radius expansion.",
        ),
    ]
    seeds["circle"] = GeometricSeed(
        id="circle",
        name="Circle",
        dimension=2,
        description="2D locus of points equidistant from a central focal point with constant radius r.",
        observable_features={
            "r": "Radius (center to boundary distance)",
            "d": "Diameter (full width across center)",
            "C": "Circumference",
            "A": "Area",
        },
        geometric_properties=[
            "Constant curvature throughout 360° boundary",
            "Infinitely many axes of reflective symmetry passing through center",
            "Tangent line at any boundary point is perpendicular to radius (tangent ⟂ radius)",
        ],
        primary_variables=["r"],
        goals=circ_goals,
    )

    # 6. Cuboid / 3D Box Seed
    cuboid_goals = [
        DiscoveryGoal(
            name="Cuboid Volume",
            predicted_feature="V",
            target_expr_str="a * b * c",
            target_ast=parse_expr_str("a * b * c"),
            mathematical_meaning="Total 3D internal capacity: product of three orthogonal edge dimensions.",
            observable_clues="Three mutually perpendicular edge axes spanning 3-space capacity.",
        ),
        DiscoveryGoal(
            name="Cuboid Surface Area",
            predicted_feature="SA",
            target_expr_str="2 * ((a * b) + ((b * c) + (c * a)))",
            target_ast=parse_expr_str("2 * ((a * b) + ((b * c) + (c * a)))"),
            mathematical_meaning="Total boundary surface area summing all 6 rectangular faces: 2(ab + bc + ca).",
            observable_clues="Three pairs of identical opposite rectangular faces.",
        ),
        DiscoveryGoal(
            name="Cuboid Edge Sum",
            predicted_feature="E",
            target_expr_str="4 * (a + b + c)",
            target_ast=parse_expr_str("4 * (a + b + c)"),
            mathematical_meaning="Total length of all 12 wireframe structural edges.",
            observable_clues="There are 4 parallel edges for each of the 3 orthogonal dimensions.",
        ),
        DiscoveryGoal(
            name="3D Space Diagonal Squared",
            predicted_feature="D^2",
            target_expr_str="a^2 + b^2 + c^2",
            target_ast=parse_expr_str("a^2 + b^2 + c^2"),
            mathematical_meaning="3D Euclidean norm squared across opposite corners: a² + b² + c².",
            observable_clues="Applying the Pythagorean theorem successively across orthogonal planes.",
        ),
    ]
    seeds["cuboid"] = GeometricSeed(
        id="cuboid",
        name="Cuboid (3D Box)",
        dimension=3,
        description="3D solid bounded by 6 rectangular faces with 3 mutually perpendicular edge directions.",
        observable_features={
            "a": "Length",
            "b": "Width",
            "c": "Height",
            "V": "Volume",
            "SA": "Surface Area",
            "D": "Space Diagonal",
        },
        geometric_properties=[
            "Three orthogonal coordinate axes (a ⟂ b ⟂ c)",
            "Three pairs of identical parallel opposite faces",
            "12 total edges, 8 vertices, 6 faces",
        ],
        primary_variables=["a", "b", "c"],
        goals=cuboid_goals,
    )

    return seeds


SEEDS = _create_default_seeds()


def get_geometric_seed(seed_id: str) -> Optional[GeometricSeed]:
    """Retrieve a geometric shape seed by ID."""
    clean = seed_id.lower().replace("-", "_").replace(" ", "_")
    return SEEDS.get(clean)


def list_geometric_seeds() -> List[GeometricSeed]:
    """Return all available geometric shape seeds."""
    return list(SEEDS.values())
