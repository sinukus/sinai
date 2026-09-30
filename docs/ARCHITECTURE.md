# Architecture

```text
Android / CLI / compatible assistant tool
                 |
          Speech/Text Gateway
                 |
        Local Context + Memory
                 |
          Cost Controller
                 |
       independent witnesses
                 |
          Cross-examination
                 |
 Evidence: web/maps/transit/rides/translation
                 |
               Judge
                 |
        ONE BEST ANSWER
                 |
           text / speech
```

The cost controller should use current price, latency, empirical task accuracy and
estimated token count. It escalates only when expected accuracy gain justifies cost.
Model independence is by underlying family, not by hosting provider.
