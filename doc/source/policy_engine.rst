.. include:: aliases.rst

.. _policy-engine:

Policy Engine
--------------

The policy engine is the component of Congress responsible for evaluating, analyzing, and enforcing policy.  To tell the policy engine what the policy is, you use the methods *insert* and *delete* (which are methods of the class congress.runtime.Runtime).

.. function:: insert(formula)

    Inserts FORMULA to the current policy.  FORMULA is a string encoding a single Datalog rule.

.. function:: delete(formula)

    Deletes FORMULA from the current policy.  FORMULA is a string encoding a single Datalog rule.


Formulas may be inserted and deleted at any time.  Once Congress has a policy that it is trying to enforce, there are a number of additional functions we can call to have Congress tell us about the current state of the cloud's policy compliance.  Many of these methods take a string encoding of Datalog as input and return a string encoding of Datalog as output.  When working in Python, we can parse a Datalog string into Python objects using **compile.parse**.

.. function:: compile.parse(string)

    Takes a string, parses it, and returns a list of compile.Rule objects representing the Datalog contained within that string.  Does not check any of the Syntactic Restrictions from :ref:`datalog`.


We can utilize the method :func:`select` to query the contents of any table, including *error*.

.. function:: select(formula)

    FORMULA is either a Datalog rule or atom.  If it is an atom, SELECT returns a string representing all instances of FORMULA that are true.  If it is a rule, it returns all instances of that rule where the body is true.

:func:`select` takes either an atom or a rule as an argument.  If it is an atom, Congress returns all instances of the atom that are true.  For example, suppose we have the following instance of the table *neutron:port*.

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.2"
"73e31d4c-a49c-11e3-be40-425861b86ab6" "10.0.0.3"
====================================== ==========

If the argument to :func:`select` is::

    'neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", x)'

then Congress would return the following statements encoded as a string.::

    neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1")
    neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.2")


If the argument to :func:`select` is a rule then Congress finds all instances of the body of the rule that are true and instantiates the variables in the head accordingly.  For example, if the rule argument were the string::

    multi_port(port) :- neutron:port(port, ip1), neutron:port(port, ip2), not equal(ip1, ip2)

then Congress would return the following string.  Notice that there are two results because there are two different reasons that "66dafde0-a49c-11e3-be40-425861b86ab6" belongs to *multi_port*.::

    multi_port("66dafde0-a49c-11e3-be40-425861b86ab6") :-
        neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1"),
        neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.2"),
        not equal("10.0.0.1", "10.0.0.2")
    multi_port("66dafde0-a49c-11e3-be40-425861b86ab6") :-
        neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.2"),
        neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1"),
        not equal("10.0.0.2", "10.0.0.1")

We can also ask Congress for an explanation as to why a row belongs to a particular table.

.. function:: explain(atom, tablenames=None, find_all=False)

    At the time of writing, this function needs an overhaul.  In theory it should return a rule describing why ATOM is true.  The head of the rule is ATOM.  The body of the rule has tables only from TABLENAMES (which if not supplied Congress is free to choose) that constitute the causes of ATOM being true.  If FIND_ALL is True, then the result is a list of all such rules.

We can also ask Congress to enumerate possible actions that will cause a given policy violation (or any other row) to be eliminated.

.. function:: remediate(atom)

    ATOM is a string representing a Datalog atom.  :func:`remediate` returns a string representing a list of action sequences that will cause ATOM to become false.

We can also ask Congress to simulate a sequence of actions and data or policy updates and answer a :func:`select` query in the resulting state.

.. function:: simulate(query, sequence)

    QUERY is any :func:`select` query.  SEQUENCE is a string of Datalog rules, described in more detail below.  SIMULATE returns select(QUERY) after applying the updates described by SEQUENCE.  Does not actually apply SEQUENCE--it only simulates its application.

SEQUENCE is a mini-programming language built out of Datalog rules.  Each Datalog rule in SEQUENCE is one of the following types.

* Data update.  q+(1) means that q(1) should be inserted.  q-(1) means that q(1) should be deleted.
* Policy update.   p+(x) :- q(x) means that p(x) :- q(x) should be inserted.  p-(x) :- q(x) means that p(x) :- q(x) should be deleted.
* Action invocation.  See :ref:`enforcement` for more details on actions.  In short, an Action is analogous to an API call that changes state in the cloud.  An action invocation is described by a Datalog rule, such as the following.::

    create_network(x, 17), options:value(17, "name", "net1") :- result(x)

Here the action being executed is *create_network(x, 17)*, where 17 is a "pointer" to the list of arguments (or options) for that API call, and the "name" argument of that argument list has value "net1".  The value of *x* depends on the return value of a previously executed action.  If the action does not depend on the previous result, you can use *true* in place of *result(x)*.







