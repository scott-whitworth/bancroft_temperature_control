###########
# This script includes all statistical analyses and graphs for Dalke et al. 2023.
# Data are named "dat1". dat1 should be used for survival analysis and development. dat for all others.
#
library(readxl)
library(car) 
library(ggplot2)
library(smatr)
library(emmeans)
library(lemon)
library(patchwork)
library(brglm2)
#create mod variables
dat<-dat1[-c(52), ] #remove tad 52 who was passed stage 42
weight<-dat$`Weight (g)`
weight_impute<-dat$Estimate_weight_g
tank<-dat$`Tank Number`
climate<-dat$Climate
conspec<-dat$Conspecific
cue<-dat$Cue
largest<-dat$head_length_cm_largest #begining size of larger tad
smallest<-dat$head_length_cm_smallest #begining size of smaller tad
stages<-dat$`Stages/day`
start_stage<-dat$`Probable Stage`
svl<-dat$SVL_cm
lnsvl<-dat$ln_svl
lnweight<-dat$ln_weight_impute
lntotlength<-dat$ln_total_length
tailmuscle<-dat$`Tail Muscle Depth_cm` # depth of muscle at deepest point
ln_tailmuscle<-dat$ln_tailmuscle
justfin<-dat$Just_fin_depth #tailfin - tailmuscle
lnjustfin<-dat$ln_justfin
fmuscleindex<-dat$smusc_index #tail muscle index (slope calculated below)
justfinindex<-dat$sjustfin_index #total- muscle index (slope calculated below)
smi_totlength<-dat$SMI_totlength
propgrowth<-dat$prop_length_largest
growthrate<-dat$growth_rate_cm_day_largest
ln_musclewidth<-dat$ln_musc_width # dorsal width of tail muscle
ln_leglength<-dat$ln_leg
swidth<-dat$swidth_index #weight based index for tail muscle width
sleg<-dat$sleg_index

### scaled body mass index from Peig and Green 2009:
#https://www.semanticscholar.org/paper/New-perspectives-for-estimating-body-condition-from-Peig-Green/5bcd97f66e36370a75abbc1af1cbccbba199de66
# first, calculate the scaling relationship between mass and SVL, total length or inter-orbital width
# need to 1) check for outliers using scatter plots, 2) test size vars for best correlation with weight
# and 3) extract the slope coefficient as the scaling component.
# uses the sma function from smatr package
# based on the natural log data

plot(lntotlength,lnweight)
sma.tot<-sma(lnweight~lntotlength, data=dat)
summary(sma.tot)

plot(lnsvl,lnweight)
sma.svl<-sma(lnweight~lnsvl, data=dat)
summary(sma.svl)


#### Calculate scaled tail indexes
plot(lnweight,ln_tailmuscle)
sma.muscle<-sma(ln_tailmuscle~lnweight, data=dat)
summary(sma.muscle)

plot(lntotlength,ln_tailmuscle)
sma.muscletot<-sma(ln_tailmuscle~lntotlength, data=dat)
summary(sma.muscletot)

plot(lnjustfin,lnweight)
sma.justfin<-sma(ln_justfin~lnweight, data=dat)
summary(sma.justfin)

plot(lnjustfin,lntotlength)
sma.justfintot<-sma(ln_justfin~lntotlength, data=dat)
summary(sma.justfintot)

plot(lnweight,ln_musclewidth)
sma.width<-sma(ln_musclewidth~lnweight, data=dat)
summary(sma.width)

plot(lntotlength,ln_musclewidth)
sma.width<-sma(ln_musclewidth~lntotlength, data=dat)
summary(sma.width)

# now leg length
plot(lnweight,ln_leglength)
sma.leg<-sma(ln_leglength~lnweight, data=dat)
summary(sma.leg)

plot(lntotlength,ln_leglength)
sma.leg<-sma(ln_leglength~lntotlength, data=dat)
summary(sma.leg)


###############
# calculate scaled indices, add to data, or save and then reload worksheet
##############


##############
# Now morphology PCA
# PCA with all variables except survival and stages
# use a scaled PCA because of different scales of measurements
morph.pc3<-prcomp(~justfinindex+sleg+swidth+fmuscleindex+weight_impute+propgrowth+growthrate+smi_totlength, data = dat, center = TRUE, scale = TRUE)
summary(morph.pc3)
morph.pc3$rotation


PC1<-morph.pc3$x[,1]
PC2<-morph.pc3$x[,2]
dat<-cbind(dat,PC1,PC2,PC3,PC4)

morph.mod3<-aov(dat$PC1~climate*conspec*cue,data = dat)
plot(morph.mod3)
summary(morph.mod3)
Anova(morph.mod3)


#Posthoc using emmeans on cue x climate interaction
morph3_posthoc_aov<-emmeans(morph.mod3, pairwise~cue|climate)
summary(morph3_posthoc_aov)

# Now with PC2
morph.mod4<-aov(dat$PC2~climate*conspec*cue,data = dat)
plot(morph.mod4)
summary(morph.mod4)
Anova(morph.mod4)

########
# now development
###
## Now with #52. Go back and change dat1 to dat (so data set with 52 is now the main dataset)
# then redefine the variables needed (treatment groups, stages)
#create mod variables

climate<-dat$Climate
conspec<-dat$Conspecific
cue<-dat$Cue
stages<-dat$`Stages/day`

devel_mod<-glm(stages~climate*conspec*cue, family = gaussian (link="log"),data = dat, na.action = na.omit)
summary(devel_mod)
Anova(devel_mod)
plot(devel_mod)

stages_posthoc<-emmeans(devel_mod, pairwise~cue|conspec|climate)
summary(stages_posthoc)
p<-emmip(devel_mod, cue~conspec|climate, CIs = TRUE)
p


#######################################
#######################################
# Survival analysis with Firth adjustment
#######################################

#load datasheet

# Create variables
clim<-dat$Climate
cons<-dat$Conspecific
fcue<-dat$Cue
survived<-dat$binary_alive


survtometbr<-glm(survived~clim+cons+fcue, family = binomial(link = logit), data = dat, na.action = na.omit,method=brglmFit )
summary(survtometbr)
Anova(survtometbr)
plot(survtometbr)



################
# Plots
###############

#PC1 and conspecific
wPCc=ggplot(dat, aes(y=PC1, x=conspec)) +
  geom_boxplot(notch = FALSE)+
  scale_fill_grey(start = 0.9,end = 0.5) +
  scale_x_discrete(labels = c('Absent','Present'))+
  xlab("Conspecific") + ylab("PC 1")+
  #stat_summary(fun="mean")+
  #base size is the font size
  theme_classic(base_size = 18)+theme(panel.grid.major = element_blank(),
                                      panel.grid.minor = element_blank(), legend.position = "none", axis.text=element_text(colour = "black"))
wPCc

### PC1 by climate and cue
clim_var<-as.factor(dat$Clim_var)
wpc1=ggplot(dat, aes(y=PC1, x=clim_var, fill = Cue)) +
  geom_boxplot(notch = FALSE)+
  scale_fill_grey(start = 0.9,end = 0.5) +
  scale_x_discrete(labels = c('Historical','Future'))+
  xlab("Climate treatment") + ylab("PC 1")+
  #base size is the font size
  theme_classic(base_size = 18)+theme(panel.grid.major = element_blank(),
                                      panel.grid.minor = element_blank(), legend.position = "right", axis.text=element_text(colour = "black"))
wpc1

#Combine both PC plots into one
patchwork=wPCc+wpc1
patchwork[[2]] = patchwork[[2]] + theme(axis.text.y = element_blank(),
                                        #axis.ticks.y = element_blank(),
                                        axis.title.y = element_blank() )

patchwork
PC_all<-patchwork #+ plot_annotation(tag_levels = "A")


#development

# for some reason, the facet wrap only works when I replicate the data and make a new factor of the variable
data_new <- dat                              # Replicate data

data_new$Clim_var<-as.factor(dat$Clim_var)
to_string <- as_labeller(c(`1` = "Historical", `2` = "Future"))

p=ggplot(data_new, aes(y=stages, x=conspec, fill=cue)) +
   geom_boxplot()+
  facet_rep_wrap( ~Clim_var, scales = "fixed", labeller = to_string, repeat.tick.labels = FALSE)+
  scale_fill_grey(start = 0.9,end = 0.5, name = "Cue") +
  scale_x_discrete(labels = c('Absent','Present'))+
  xlab("Conspecific present") + ylab("Developmental stages/d")+
  #base size is the font size
  theme_classic(base_size = 18)+theme(panel.grid.major = element_blank(),panel.grid.minor = element_blank(),legend.position = "right", axis.text=element_text(colour = "black"), strip.background = element_blank())
p


######
# graphing additive interactions 
# note that stages are positive values (higher than controls)
####

# load datasheet with observed and expected effects ("for Tekin graph" in dataset)

figdat<-dat2
treats<-figdat$Treatment
comparison<-figdat$Comparison
orderlist<-figdat$Order
Mass<-figdat$Mass
Growth<-figdat$Growth
Growth_rate<-figdat$Growth_rate
SMI<-figdat$SMI
Tail_musc_depth<-figdat$Tail_musc_depth
Tail_musc_width<-figdat$Tail_musc_width
Tail_fin_depth<-figdat$Tail_fin_depth
Leg_length<-figdat$Leg_length
Stages_day<-figdat$Stages_day


to_string <- as_labeller(c("1Climate × Conspecific × Cue" = "Climate × Conspecific × Cue", "2Climate × Conspecific" = "Climate × Conspecific","3Climate × Cue" = "Climate × Cue","4Conspecific × Cue"="Conspecific × Cue"))


#weight, all three stressors together
data_new <- figdat # Replicate data
treats<-data_new$Treatment
w.three=ggplot(data_new, aes(y=Mass, x=orderlist, fill = treats)) +
  geom_bar(stat = "identity", color = "black")+
  facet_rep_grid( .~Comparison, scales = "free_x",labeller = to_string,repeat.tick.labels = FALSE)+
  scale_x_continuous(
    breaks = figdat$Order,
    labels = figdat$Treatment,
    expand = c(0,0)
  ) +
  ylim(-0.8, 0)+
  xlab(element_blank()) +  
  ylab("Mass")+
  scale_fill_grey(limits = c("Climate","Conspecific", "Fish cue", "Combined"), name = "Treatments")+
  #base size is the font size
  theme_classic(base_size = 12)+theme(panel.grid.major = element_blank(),
                                 panel.grid.minor = element_blank(),
                                 axis.text.x = element_blank(),
                                 axis.ticks.x = element_blank(),
                                 legend.position = "none", axis.text=element_text(colour = "black"),strip.background = element_blank())

w.three

#Growth data
g.three=ggplot(data_new, aes(y=Growth, x=orderlist, fill = treats)) +
  geom_bar(stat = "identity", color = "black")+
  facet_rep_grid( .~Comparison, scales = "free_x",repeat.tick.labels = FALSE)+
  #scale_x_continuous(
  #breaks = figdat$Order,
  #labels = figdat$Treatment...2,
  #expand = c(0,0)
  #) +
  ylim(-0.8, 0)+
  xlab(element_blank()) + 
  ylab("Growth")+
  scale_fill_grey(limits = c("Climate","Conspecific", "Fish cue", "Combined", "Additive expectation"), name = "Treatments")+
  #base size is the font size
  theme_classic(base_size = 12)+theme(panel.grid.major = element_blank(),
                                      panel.grid.minor = element_blank(),
                                      axis.text.x = element_blank(),
                                      axis.ticks.x = element_blank(),
                                      legend.position = "none", axis.text=element_text(colour = "black"),
                                      strip.background = element_blank(),
                                      strip.text = element_blank())


g.three

#Growth rate data
gr.three=ggplot(data_new, aes(y=Growth_rate, x=orderlist, fill = treats)) +
  geom_bar(stat = "identity", color = "black")+
  facet_rep_grid( .~Comparison, scales = "free_x",repeat.tick.labels = FALSE)+
  scale_x_continuous(
    breaks = figdat$Order,
    labels = figdat$Treatment,
    expand = c(0,0)
  ) +
  ylim(-0.8, 0)+
  xlab(element_blank()) + 
  ylab("Growth rate")+
  scale_fill_grey(limits = c("Climate","Conspecific", "Fish cue", "Combined", "Additive expectation"), name = "Treatments")+
  #base size is the font size
  theme_classic(base_size = 12)+theme(panel.grid.major = element_blank(),
                                      panel.grid.minor = element_blank(),
                                      axis.text.x = element_blank(),
                                      axis.ticks.x = element_blank(),
                                      legend.position = "none", axis.text=element_text(colour = "black"),
                                      strip.background = element_blank(),
                                      strip.text = element_blank())


gr.three

#Scaled mass index data
smi.three=ggplot(data_new, aes(y=SMI, x=orderlist, fill = treats)) +
  geom_bar(stat = "identity", color = "black")+
  facet_rep_grid( .~Comparison, scales = "free_x",repeat.tick.labels = FALSE)+
  scale_x_continuous(
    breaks = figdat$Order,
    labels = figdat$Treatment,
    expand = c(0,0)
  ) +
  ylim(-0.8, 0.8)+
  xlab(element_blank()) +
  ylab("SMI")+
  scale_fill_grey(limits = c("Climate","Conspecific", "Fish cue", "Combined", "Additive expectation"), name = "Treatments")+
  #base size is the font size
  theme_classic(base_size = 12)+theme(panel.grid.major = element_blank(),
                                      panel.grid.minor = element_blank(),
                                      axis.text.x = element_blank(),
                                      axis.ticks.x = element_blank(),
                                      legend.position = "none", axis.text=element_text(colour = "black"),
                                      strip.background = element_blank(),
                                      strip.text = element_blank())

smi.three


#Tail muscle depth index data
tmd.three=ggplot(data_new, aes(y=Tail_musc_depth, x=orderlist, fill = treats)) +
  geom_bar(stat = "identity", color = "black")+
  facet_rep_grid( .~Comparison, scales = "free_x",repeat.tick.labels = FALSE)+
  scale_x_continuous(
    breaks = figdat$Order,
    labels = figdat$Treatment,
    expand = c(0,0)
  ) +
  ylim(-0.8, 0)+
  xlab(element_blank()) +
  ylab("Muscle depth")+
  scale_fill_grey(limits = c("Climate","Conspecific", "Fish cue", "Combined", "Additive expectation"), name = "Treatments")+
  #base size is the font size
  theme_classic(base_size = 12)+theme(panel.grid.major = element_blank(),
                                       panel.grid.minor = element_blank(),
                                       axis.text.x = element_blank(),
                                       axis.ticks.x = element_blank(),
                                       legend.position = "none", axis.text=element_text(colour = "black"),
                                       strip.background = element_blank(),
                                       strip.text = element_blank())

tmd.three

#Tail muscle width index data
tmw.three=ggplot(data_new, aes(y=Tail_musc_width, x=orderlist, fill = treats)) +
  geom_bar(stat = "identity", color = "black")+
  facet_rep_grid( .~Comparison, scales = "free_x",repeat.tick.labels = FALSE)+
  scale_x_continuous(
    breaks = figdat$Order,
    labels = figdat$Treatment,
    expand = c(0,0)
  ) +
  ylim(-0.8, 0)+
  xlab(element_blank()) +
  ylab("Muscle width")+
  scale_fill_grey(limits = c("Climate","Conspecific", "Fish cue", "Combined", "Additive expectation"), name = "Treatments")+
  #base size is the font size
  theme_classic(base_size = 12)+theme(panel.grid.major = element_blank(),
                                      panel.grid.minor = element_blank(),
                                      axis.text.x = element_blank(),
                                      axis.ticks.x = element_blank(),
                                      legend.position = "none", axis.text=element_text(colour = "black"),
                                      strip.background = element_blank(),
                                      strip.text = element_blank())

tmw.three


#Tail fin depth index data
tfd.three=ggplot(data_new, aes(y=Tail_fin_depth, x=orderlist, fill = treats)) +
  geom_bar(stat = "identity", color = "black")+
  facet_rep_grid( .~Comparison, scales = "free_x",repeat.tick.labels = FALSE)+
  scale_x_continuous(
    breaks = figdat$Order,
    labels = figdat$Treatment,
    expand = c(0,0)
  ) +
  ylim(-0.8, 0)+
  xlab(element_blank()) +
  ylab("Fin depth")+
  scale_fill_grey(limits = c("Climate","Conspecific", "Fish cue", "Combined", "Additive expectation"), name = "Treatments")+
  #base size is the font size
  theme_classic(base_size = 12)+theme(panel.grid.major = element_blank(),
                                      panel.grid.minor = element_blank(),
                                      axis.text.x = element_blank(),
                                      axis.ticks.x = element_blank(),
                                      legend.position = "none", axis.text=element_text(colour = "black"),
                                      strip.background = element_blank(),
                                      strip.text = element_blank())

tfd.three

#Leg index data
l.three=ggplot(data_new, aes(y=Leg_length, x=orderlist, fill = treats)) +
  geom_bar(stat = "identity", color = "black")+
  facet_rep_grid( .~Comparison, scales = "free_x",repeat.tick.labels = FALSE)+
  scale_x_continuous(
    breaks = figdat$Order,
    labels = figdat$Treatment,
    expand = c(0,0)
  ) +
  ylim(-.8, 0)+
  xlab(element_blank()) +
  ylab("Leg length")+
  scale_fill_grey(limits = c("Climate","Conspecific", "Fish cue", "Combined", "Additive expectation"), name = "Treatments")+
  #base size is the font size
  theme_classic(base_size = 12)+theme(panel.grid.major = element_blank(),
                                      panel.grid.minor = element_blank(),
                                      axis.text.x = element_blank(),
                                      axis.ticks.x = element_blank(),
                                      legend.position = "none", axis.text=element_text(colour = "black"),
                                      strip.background = element_blank(),
                                      strip.text = element_blank())

l.three


#Stages data
s.three=ggplot(data_new, aes(y=Stages_day, x=orderlist, fill = treats)) +
  geom_bar(stat = "identity", color = "black")+
  facet_rep_grid( .~Comparison, scales = "free_x",repeat.tick.labels = FALSE)+
  scale_x_continuous(
    breaks = figdat$Order,
    labels = figdat$Treatment,
    expand = c(0,0)
  ) +
  ylim(0, 0.8)+
  xlab("Treatment") + 
  ylab("Development")+
  scale_fill_grey(limits = c("Climate","Conspecific", "Fish cue", "Combined", "Additive expectation"), name = "Treatments")+
  #base size is the font size
  theme_classic(base_size = 12)+theme(panel.grid.major = element_blank(),
                                      panel.grid.minor = element_blank(),
                                      axis.text.x = element_text(angle = 90),
                                      legend.position = "none", axis.text=element_text(colour = "black"),
                                      strip.background = element_blank(),
                                      strip.text = element_blank())

                                    
                                    
s.three

####
# now combine using Patchwork
##

all.grid<-w.three/g.three/gr.three/smi.three/tmd.three/tmw.three/tfd.three/l.three/s.three
all.grid
ggsave(all.grid, file='/Volumes/GoogleDrive/Shared drives/Bancroft Lab/Project Folders/Summer 2019/Murdock CC invasion 2019/figures/2019_all_gridded_response_2022.tiff', width = 10, height=16, dpi=600)

# FWS requires minus signs to be en dashes instead of hyphens. Saving as a PDF converts hyphens to en dashes
# apparently. Then you can open the PDF in photoshop.

