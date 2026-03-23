library(ggplot2)
library(scales)
library(patchwork)

# --------------------------
# Top plot: enforceability
# --------------------------
df1 <- data.frame(
  Benchmark = rep(c("tau2-Bench", "Car-Bench", "MedAgentBench"), each = 3),
  Category = rep(c("Out of Scope", "Not Enforceable", "Enforceable"), times = 3),
  Value = c(
    69, 9, 42,
    0, 1, 17,
    31, 23, 34
  )
)

df1$Benchmark <- factor(
  df1$Benchmark,
  levels = c("tau2-Bench", "Car-Bench", "MedAgentBench")
)

df1 <- do.call(rbind, lapply(split(df1, df1$Benchmark), function(d) {
  d$Prop <- d$Value / sum(d$Value)
  d$Label <- ifelse(
    d$Prop >= 0.08,
    paste0(d$Value, " (", round(100 * d$Prop, 1), "%)"),
    ""
  )
  d
}))

colors1 <- c( # red blue green
  "Out of Scope" = "#e25a5c",
  "Not Enforceable" = "#4d91c8",
  "Enforceable"  = "#4DAF4A"
)

p1 <- ggplot(df1, aes(x = Benchmark, y = Prop, fill = Category)) +
  geom_col(width = 0.7, color = "white", linewidth = 0.8) +
  geom_text(
    aes(label = Label),
    position = position_stack(vjust = 0.5),
    size = 4.5,
    family = "serif"
  ) +
  scale_fill_manual(values = colors1) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    expand = c(0, 0)
  ) +
  scale_x_discrete(
    labels = c(
      "tau2-Bench" = expression(tau^2 * "-Bench"),
      "Car-Bench" = "Car-Bench",
      "MedAgentBench" = "MedAgentBench"
    )
  ) +
  labs(x = NULL, y = "Share", fill = NULL) +
  theme_classic(base_size = 15, base_family = "serif") +
  theme(
    axis.text.x = element_text(size = 15, face = "bold"),
    axis.text.y = element_text(size = 15),
    axis.title.y = element_text(size = 15),
    legend.position = "top",
    legend.text = element_text(size = 14),
    panel.border = element_blank()
  )


ggsave("stacked_bar_benchmarks_enforceability.pdf", p1, width = 8, height = 4, bg = "white")

# --------------------------
# Bottom plot: guardrail types
# --------------------------
df2 <- data.frame(
  Benchmark = rep(c("tau2-Bench", "Car-Bench", "MedAgentBench"), each = 7),
  Category = rep(c(
    "User Confirmation",
    "Schema Constraint",
    "Response Template",
    "API Validation",
    "Information Flow",
    "Temporal Logic",
    "Combination of Guardrails"
  ), times = 3),
  Value = c(
    1, 6, 1, 34, 0, 0, 0,   # tau2-Bench
    3, 0, 2, 11, 0, 0, 1,   # Car-Bench
    5, 2, 6, 16, 3, 2, 0    # MedAgentBench
  )
)

df2$Benchmark <- factor(
  df2$Benchmark,
  levels = c("tau2-Bench", "Car-Bench", "MedAgentBench")
)

df2$Category <- factor(
  df2$Category,
  levels = c(
    "API Validation",
    "Schema Constraint",
    "Temporal Logic",
    "Information Flow",
    "User Confirmation",
    "Response Template",
    "Combination of Guardrails"
  )
)

df2 <- do.call(rbind, lapply(split(df2, df2$Benchmark), function(d) {
  d$Prop <- d$Value / sum(d$Value)
  d$Label <- ifelse(
    d$Prop >= 0.08,
    paste0(d$Value, " (", round(100 * d$Prop, 1), "%)"),
    ""
  )
  d
}))

colors2 <- c(
  "User Confirmation" = "#e25a5c",
  "Schema Constraint" = "#4d91c8",
  "Response Template" = "#4DAF4A",
  "API Validation" = "#ad60b9",
  "Information Flow" =  "#FF7F00",
  "Temporal Logic" = "#FFFF33",
  "Combination of Guardrails" =  "#c17447"
)

p2 <- ggplot(df2, aes(x = Benchmark, y = Prop, fill = Category)) +
  geom_col(width = 0.7, color = "white", linewidth = 0.8) +
  geom_text(
    aes(label = Label),
    position = position_stack(vjust = 0.5),
    size = 4.5,
    family = "serif"
  ) +
  scale_fill_manual(values = colors2) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    expand = c(0, 0)
  ) +
  scale_x_discrete(
    labels = c(
      "tau2-Bench" = expression(tau^2 * "-Bench"),
      "Car-Bench" = "Car-Bench",
      "MedAgentBench" = "MedAgentBench"
    )
  ) +
  guides(fill = guide_legend(nrow = 3, byrow = TRUE)) +
  labs(x = NULL, y = "Share", fill = NULL) +
  theme_classic(base_size = 15, base_family = "serif") +
  theme(
    axis.text.x = element_text(size = 15, face = "bold"),
    axis.text.y = element_text(size = 15),
    axis.title.y = element_text(size = 15),
    legend.position = "top",
    legend.text = element_text(size = 14),
    panel.border = element_blank()
  )

# --------------------------
# Combine vertically
# --------------------------
p <- p1 / p2 + plot_layout(heights = c(1, 1))

print(p)

# p2
ggsave("stacked_bar_benchmarks_guardrail_types.pdf", p2, width = 8, height = 5, bg = "white")

ggsave("stacked_bar_benchmarks_two_panels.pdf", p, width = 8, height = 8.5, bg = "white")