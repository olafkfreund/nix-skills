let
  x = 1;
  shallow = { nested = { a = 1; b = 2; }; } // { nested = { a = 3; }; };
  defaults = args@{ a ? 23, ... }: [ a args ];
in
assert (with { x = 2; }; x) == 1;
assert shallow.nested == { a = 3; };
assert defaults { } == [ 23 { } ];
assert defaults { a = 7; } == [ 7 { a = 7; } ];
assert (let unused = throw "must remain lazy"; in 42) == 42;
assert ({ good = 1; bad = throw "unforced"; }).good == 1;
assert !(builtins.tryEval (builtins.deepSeq { bad = throw "forced"; } true)).success;
assert "answer=${builtins.toString 42}" == "answer=42";
assert builtins.map (n: n + 1) [ 1 2 ] == [ 2 3 ];
true
