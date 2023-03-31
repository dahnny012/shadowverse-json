{
    "effects": [
        {
            type: "fanfare",
            effect: {
                type: "Rally",
                condition: "",
                effect: {
                    type: "Summon",
                    units: [
                        {
                            quantifier: "1",
                            unitName: "",
                            effect: {
                                type: "then",
                                effect: {
                                    type: "evolve",
                                    target: ["summon", "self"]
                                }
                            }
                        }
                    ]
                }
            }
        }
    ]
}