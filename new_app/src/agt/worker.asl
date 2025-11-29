{ include("$jacamo/templates/common-cartago.asl") }
{ include("$jacamo/templates/common-moise.asl") }
{ include("$moise/asl/org-obedient.asl") }


-!_::NoPlan[error(no_relevant)] <-
    .print("Não sei como fazer ", NoPlan, ". Vou pedir para ", coord, ". :(");
    .send(coordinator, askHow, {+!NoPlan[_]}, Result);
    .add_plan(Result);
    .print(Result);
    !NoPlan.
