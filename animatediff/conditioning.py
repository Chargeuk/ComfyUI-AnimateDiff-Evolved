from torch import Tensor

from .utils_motion import LoraHookGroup


class COND_CONST:
    KEY_LORA_HOOK = "lora_hook"
    KEY_DEFAULT_COND = "default_cond"

    COND_AREA_DEFAULT = "default"
    COND_AREA_MASK_BOUNDS = "mask bounds"
    _LIST_COND_AREA = [COND_AREA_DEFAULT, COND_AREA_MASK_BOUNDS]


class ScheduleCond:
    def __init__(self, start_percent: float, end_percent: float):
        self.start_percent = start_percent
        self.end_percent = end_percent


def conditioning_set_values(conditioning, values={}):
    c = []
    for t in conditioning:
        n = [t[0], t[1].copy()]
        for k in values:
            n[1][k] = values[k]
        c.append(n)
    return c

def set_lora_hook_for_conditioning(conditioning, lora_hook: LoraHookGroup):
    if lora_hook is None:
        return conditioning
    return conditioning_set_values(conditioning, {COND_CONST.KEY_LORA_HOOK: lora_hook})

def set_schedule_for_conditioning(conditioning, start_percent: float, end_percent: float):
    return conditioning_set_values(conditioning, {"start_percent": start_percent, "end_percent": end_percent})

def set_mask_for_conditioning(conditioning, mask: Tensor, set_cond_area: str, strength: float):
    set_area_to_bounds = False
    if set_cond_area != COND_CONST.COND_AREA_DEFAULT:
        set_area_to_bounds = True
    if len(mask.shape) < 3:
        mask = mask.unsqueeze(0)

    return conditioning_set_values(conditioning, {"mask": mask,
                                               "set_area_to_bounds": set_area_to_bounds,
                                               "mask_strength": strength})

def combine_conditioning(conds: list):
    combined_conds = []
    for cond in conds:
        combined_conds.extend(cond)
    return combined_conds

def set_mask_conds(conds: list, mask: Tensor, strength: float, set_cond_area: str, opt_lora_hook: LoraHookGroup=None):
    masked_conds = []
    for c in conds:
        # first, apply lora_hook to conditioning, if provided
        c = set_lora_hook_for_conditioning(c, opt_lora_hook)
        # finally, apply mask to conditioning and store
        masked_conds.append(set_mask_for_conditioning(conditioning=c, mask=mask, strength=strength, set_cond_area=set_cond_area))
    return masked_conds

def set_mask_and_combine_conds(conds: list, new_conds: list, mask: Tensor, strength: float, set_cond_area: str, opt_lora_hook: LoraHookGroup=None):
    combined_conds = []
    for c, masked_c in zip(conds, new_conds):
        # first, apply lora_hook to new conditioning, if provided
        masked_c = set_lora_hook_for_conditioning(masked_c, opt_lora_hook)
        # next, apply mask to new conditioning
        masked_c = set_mask_for_conditioning(conditioning=masked_c, mask=mask, set_cond_area=set_cond_area, strength=strength)
        # finally, combine with existing conditioning and store
        combined_conds.append(combine_conditioning([c, masked_c]))
    return combined_conds

def set_unmasked_and_combine_conds(conds: list, new_conds: list, opt_lora_hook: LoraHookGroup):
    combined_conds = []
    for c, new_c in zip(conds, new_conds):
        # first, apply lora_hook to new conditioning, if provided
        new_c = set_lora_hook_for_conditioning(new_c, opt_lora_hook)
        # next, add default_cond key to cond so that during sampling, it can be identified
        new_c = conditioning_set_values(new_c, {COND_CONST.KEY_DEFAULT_COND: True})
        # finally, combine with existing conditioning and store
        combined_conds.append(combine_conditioning([c, new_c]))
    return combined_conds
