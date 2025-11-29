{ include("$jacamo/templates/common-cartago.asl") }
{ include("$jacamo/templates/common-moise.asl") }
{ include("$moise/asl/org-obedient.asl") }


+!square <- 
    ?goalArgument(_, square, "N", V);
    .wait(30000);
    X=V*V;
    .print(V, " ao quadrado é ", X).

+!init <-
    N = math.round(math.random(25)+1);
    .print("Iniciando cálculo de ", N, " ao quadrado..");
    setArgumentValue(square,"N",N).

// +!calculate <- .print("Finalizado").

// +oblUnfulfilled( obligation(Ag,_,commited(Sch,square,Ag),_ ) )[_]  // it is the case that a bid was not achieved

//    <- .print("Participant ",Ag," didn't bid on time! S/he will be placed in a block list").
//        // TODO: implement a block list artifact
//     //    admCommand("goalSatisfied(bid)")[artifact_id(AId)]. // go on in the scheme....
