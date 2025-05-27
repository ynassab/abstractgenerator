latex_to_html_map = {
    # Lowercase Greek letters
    r'\\alpha': '&alpha;',
    r'\\beta': '&beta;',
    r'\\gamma': '&gamma;',
    r'\\delta': '&delta;',
    r'\\epsilon': '&epsilon;',
    r'\\varepsilon': '&epsilon;',  # Including special variable forms
    r'\\zeta': '&zeta;',
    r'\\eta': '&eta;',
    r'\\theta': '&theta;',
    r'\\vartheta': '&theta;',
    r'\\iota': '&iota;',
    r'\\kappa': '&kappa;',
    r'\\lambda': '&lambda;',
    r'\\mu': '&mu;',
    r'\\nu': '&nu;',
    r'\\xi': '&xi;',
    r'\\omicron': '&omicron;',
    r'\\pi': '&pi;',
    r'\\rho': '&rho;',
    r'\\varrho': '&rho;',
    r'\\sigma': '&sigma;',
    r'\\tau': '&tau;',
    r'\\upsilon': '&upsilon;',
    r'\\phi': '&phi;',
    r'\\varphi': '&phi;',
    r'\\chi': '&chi;',
    r'\\psi': '&psi;',
    r'\\omega': '&omega;',

    # Uppercase Greek letters
    r'\\Alpha': '&Alpha;',
    r'\\Beta': '&Beta;',
    r'\\Gamma': '&Gamma;',
    r'\\Delta': '&Delta;',
    r'\\Epsilon': '&Epsilon;',
    r'\\Zeta': '&Zeta;',
    r'\\Eta': '&Eta;',
    r'\\Theta': '&Theta;',
    r'\\Iota': '&Iota;',
    r'\\Kappa': '&Kappa;',
    r'\\Lambda': '&Lambda;',
    r'\\Mu': '&Mu;',
    r'\\Nu': '&Nu;',
    r'\\Xi': '&Xi;',
    r'\\Omicron': '&Omicron;',
    r'\\Pi': '&Pi;',
    r'\\Rho': '&Rho;',
    r'\\Sigma': '&Sigma;',
    r'\\Tau': '&Tau;',
    r'\\Upsilon': '&Upsilon;',
    r'\\Phi': '&Phi;',
    r'\\Chi': '&Chi;',
    r'\\Psi': '&Psi;',
    r'\\Omega': '&Omega;',

    # Arrow symbols
    r'\\leftarrow': '&larr;',          # Left arrow
    r'\\Leftarrow': '&lArr;',          # Left double arrow
    r'\\rightarrow': '&rarr;',         # Right arrow
    r'\\Rightarrow': '&rArr;',         # Right double arrow
    r'\\leftrightarrow': '&harr;',     # Left right arrow
    r'\\Leftrightarrow': '&hArr;',     # Left right double arrow
    r'\\uparrow': '&uarr;',            # Up arrow
    r'\\downarrow': '&darr;',          # Down arrow
    r'\\Uparrow': '&uArr;',            # Up double arrow
    r'\\Downarrow': '&dArr;',          # Down double arrow
    r'\\Updownarrow': '&vArr;',        # Up down double arrow
    r'\\mapsto': '&map;',              # Maps to arrow (mapsto symbol)
    r'\\longmapsto': '&xmap;',         # Long right array from bar (not a perfect match)
    r'\\nearrow': '&nearr;',           # North east arrow
    r'\\searrow': '&searr;',           # South east arrow
    r'\\swarrow': '&swarr;',           # South west arrow
    r'\\nwarrow': '&nwarr;',           # North west arrow
    r'\\leftharpoonup': '&lharu;',     # Left harpoon up
    r'\\rightharpoonup': '&rharu;',    # Right harpoon up
    r'\\leftharpoondown': '&lhard;',   # Left harpoon down
    r'\\rightharpoondown': '&rhard;',  # Right harpoon down
    r'\\rightleftharpoons': '&rlhar;', # Left-Right harpoons

    # Binary operations and relationship symbols
    r'\\times': '&times;',        # Multiplication sign
    r'\\cdot': '&middot;',        # Middle dot
    r'\\div': '&divide;',         # Division sign
    r'\\cap': '&cap;',            # Intersection
    r'\\cup': '&cup;',            # Union
    r'\\neq': '&ne;',             # Not equal
    r'\\leq': '&le;',             # Less than or equal
    r'\\geq': '&ge;',             # Greater than or equal
    r'\\in': '&isin;',            # Element of
    r'\\perp': '&perp;',          # Perpendicular
    r'\\notin': '&notin;',        # Not element of
    r'\\subset': '&sub;',         # Subset
    r'\\simeq': '&sime;',         # Similar to or approximately equal
    r'\\approx': '&asymp;',       # Approximately equal
    r'\\wedge': '&and;',          # Logical and
    r'\\vee': '&or;',             # Logical or
    r'\\oplus': '&oplus;',        # Direct sum
    r'\\otimes': '&otimes;',      # Tensor product
    r'\\Box': '&square;',         # Square (unsure about HTML equivalent; please verify)
    r'\\boxtimes': '&boxtimes;',  # Box multiplication (unsure about HTML equivalent; please verify)
    r'\\equiv': '&equiv;',        # Identical to
    r'\\cong': '&cong;',          # Congruent to
    r'\\propto': '&prop;',         # Proportional to

    # Miscellaneous symbols
    r'\\infty': '&infin;',          # Infinity
    r'\\forall': '&forall;',        # For all
    r'\\Re': '&real;',              # Real part symbol
    r'\\Im': '&image;',              # Imaginary part symbol
    r'\\nabla': '&nabla;',          # Nabla (del operator)
    r'\\exists': '&exist;',         # There exists
    r'\\partial': '&part;',         # Partial derivative
    r'\\nexists': '&nexist;',       # There does not exist
    r'\\emptyset': '&empty;',       # Empty set
    r'\\varnothing': '&empty;',     # Var nothing (usually same as empty set)
    r'\\wp': '&weierp;',            # Weierstrass p
    r'\\complement': '&comp;',      # Complement symbol
    r'\\neg': '&not;',              # Negation
    r'\\cdots': '&ctdot;',          # Centered dots
    r'\\square': '&#9633;',         # White Square
    r'\\surd': '&radic;',           # Square root
    r'\\blacksquare': '&#9632;',    # Black square
    r'\\triangle': '&triangle;',    # Triangle
}

