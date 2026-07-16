import { tokens } from '../../theme'

export type TierNumber = 1 | 2 | 3

export const TIER_COLORS: Record<TierNumber, {
  solid: string
  subtle: string
  text:   string
  label:  string
}> = {
  1: { solid: tokens.brand.primaryLight,  subtle: tokens.brand.primarySubtle,  text: tokens.brand.primary,      label: 'Tier 1' },
  2: { solid: tokens.brand.secondary,     subtle: tokens.brand.secondarySubtle, text: tokens.brand.secondaryText, label: 'Tier 2' },
  3: { solid: tokens.brand.danger,        subtle: tokens.brand.dangerSubtle,    text: tokens.brand.dangerText,    label: 'Tier 3' },
}
