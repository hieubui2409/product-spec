```mermaid
flowchart BT
  classDef deferred stroke-dasharray: 4 2,opacity:0.6
  PRODUCT["PRODUCT: Acme Shop"]
  BRD_G1["BRD-G1\nOnboard 100 boutique brands in 12 months"]
  BRD_G2["BRD-G2\nAchieve 80% 90-day repeat-purchase rate"]
  PRD_CHECKOUT["PRD-CHECKOUT\n"]
  PRD_CHECKOUT_E1["PRD-CHECKOUT-E1\n"]
  PRD_CHECKOUT_E1_S1["PRD-CHECKOUT-E1-S1\n"]
  PRD_CHECKOUT --> BRD_G1
  PRD_CHECKOUT --> BRD_G2
  PRD_CHECKOUT_E1 --> PRD_CHECKOUT
  PRD_CHECKOUT_E1_S1 --> PRD_CHECKOUT_E1
  BRD_G1 --> PRODUCT
  BRD_G2 --> PRODUCT
```
