# Algorithme — affectation hebdomadaire optimale

## 1. Énoncé formel

On dispose de deux suites d'entiers positifs ou nuls :

- `l = (l_1, …, l_n)` — profits d'un travail **facile** ;
- `h = (h_1, …, h_n)` — profits d'un travail **difficile**.

Pour chaque semaine `i ∈ {1, …, n}`, on choisit une action `x_i ∈ {facile, difficile, repos}`, avec la contrainte :

> `x_i = difficile ⟹ i = 1 ou x_{i-1} = repos`.

Le gain d'un planning `x = (x_1, …, x_n)` est

```
G(x) = Σ_i [x_i = facile] · l_i + [x_i = difficile] · h_i
```

On cherche `x*` maximisant `G`.

## 2. Sous-structure optimale

Soit `OPT(i)` le gain maximal atteignable sur les semaines `1..i` (avec la même contrainte). On montre que `OPT` satisfait la récurrence :

```
OPT(0) = 0
OPT(i) = max(
    OPT(i-1),           # (R)  repos  en semaine i
    OPT(i-1) + l_i,     # (F)  facile en semaine i
    OPT(i-2) + h_i      # (D)  difficile en semaine i (force repos en i-1)
)
```

avec la convention `OPT(-1) = 0` pour le cas `i = 1`.

### Preuve (principe d'optimalité)

Soit `x*` un planning optimal sur `1..i`.

- **Cas (R)** : si `x*_i = repos`, alors `(x*_1, …, x*_{i-1})` est un planning faisable sur `1..i-1` de gain `G(x*) - 0 = OPT(i)`. Il est nécessairement optimal sur `1..i-1` (sinon on pourrait l'améliorer et contredire l'optimalité de `x*`). Donc `OPT(i) = OPT(i-1)`.
- **Cas (F)** : symétrique, `OPT(i) = OPT(i-1) + l_i`.
- **Cas (D)** : `x*_i = difficile` impose `x*_{i-1} = repos` (si `i ≥ 2`). Alors `(x*_1, …, x*_{i-2})` est un planning faisable sur `1..i-2` de gain `G(x*) - h_i` (le repos en `i-1` ne rapporte rien). Par le même argument, `G(x*) - h_i = OPT(i-2)`, d'où `OPT(i) = OPT(i-2) + h_i`. Si `i = 1`, pas de contrainte à satisfaire, et `OPT(1) = h_1`.

Comme `x*_i` est nécessairement dans `{R, F, D}`, `OPT(i)` est le max des trois valeurs. ∎

## 3. Remarque : le cas « repos » est-il utile ?

Si `l_i ≥ 0` pour tout `i`, `OPT(i-1) + l_i ≥ OPT(i-1)`, donc `(R)` est toujours dominé par `(F)` et peut être omis **pour le calcul de `OPT`**. Mais il reste nécessaire **pour la reconstruction** : une semaine peut se retrouver en repos *non parce qu'on l'a choisie*, mais parce que la semaine suivante est difficile.

Garder `(R)` dans le `max` rend le solveur robuste à des profits négatifs (par ex. si un travail facile coûte plus qu'il ne rapporte).

## 4. Reconstruction du planning

On mémorise pendant la phase aller le choix optimal `choice[i] ∈ {R, F, D}`. En phase retour :

```
i ← n
tant que i ≥ 1 :
    schedule[i] ← choice[i]
    si choice[i] = D :
        schedule[i-1] ← R          # repos imposé
        i ← i - 2
    sinon :
        i ← i - 1
```

Cette approche évite la comparaison d'égalités délicates entre `OPT(i)` et les trois candidats, et garantit un planning cohérent avec le `dp`.

## 5. Complexité

- **Temps** : `O(n)` — une passe avant, une passe arrière.
- **Mémoire** : `O(n)` — nécessaire pour reconstruire le planning. En ne renvoyant que le gain, `O(1)` suffirait (deux variables roulantes `prev`, `prev_prev`).

## 6. Exemple détaillé

Soit `l = [10, 1, 10, 10]`, `h = [5, 50, 5, 50]`.

| i | `OPT(i-1)` | `OPT(i-2)` | `+l_i` | `+h_i` | max | choix |
|---|-----------:|-----------:|-------:|-------:|----:|:-----:|
| 1 |          — |          — |     10 |      5 |  10 |   F   |
| 2 |         10 |          0 |     11 |     50 |  50 |   D   |
| 3 |         50 |         10 |     60 |     15 |  60 |   F   |
| 4 |         60 |         50 |     70 |    100 | 100 |   D   |

Reconstruction depuis `i = 4` : D → repos en 3 → i = 2 ; choice[2] = D → repos en 1 → i = 0. Planning : `[R, D, R, D]`, gain `0 + 50 + 0 + 50 = 100`. ✓
