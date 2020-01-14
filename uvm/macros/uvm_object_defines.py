
from ..base.uvm_registry import *
from ..base.sv import sv

from ..base.uvm_object_globals import *


def uvm_object_utils(T):
    Ts = T.__name__
    m_uvm_object_registry_internal(T,Ts)
    m_uvm_object_create_func(T, Ts)
    m_uvm_get_type_name_func(T, Ts)


def uvm_component_utils(T):
    #if not __name__ in T:
    #    raise Exception("No __name__ found in {}".format(T))
    Ts = T.__name__
    m_uvm_component_registry_internal(T, Ts)
    m_uvm_get_type_name_func(T, Ts)


def m_uvm_get_type_name_func(T, Ts):
    setattr(T, 'type_name', Ts)

    def get_type_name(self):
        return Ts
    setattr(T, 'get_type_name', get_type_name)


def m_uvm_component_registry_internal(T,S):
    setattr(T, 'type_id', UVMComponentRegistry(T, S))

    def type_id():
        return T.type_id

    @classmethod
    def get_type(T):
        return T.type_id.get()
    setattr(T, 'get_type', get_type)

    def get_object_type(self):
        return T.type_id.get()
    setattr(T, 'get_object_type', get_object_type)


def m_uvm_object_registry_internal(T,S):
    setattr(T, 'type_id', UVMObjectRegistry(T, S))

    def type_id():
        return T.type_id

    @classmethod
    def get_type(T):
        return T.type_id.get()
    setattr(T, 'get_type', get_type)

    def get_object_type(self):
        return T.type_id.get()
    setattr(T, 'get_object_type', get_object_type)


def m_uvm_object_create_func(T,S):
    # pass
    def create(self, name=""):
        return T(name)
    setattr(T, 'create', create)


# Needed to make uvm_field_* macros work with similar args as in SV,
# stores the class object of last uvm_object_utils_begin(...)
__CURR_OBJ = None


def uvm_component_utils_begin(T):
    global __CURR_OBJ
    __CURR_OBJ = T
    uvm_component_utils(T)
    uvm_field_utils_start(T)

def uvm_component_utils_end(T):
    global __CURR_OBJ
    if __CURR_OBJ is not T:
        raise Exception('Expected: ' + str(__CURR_OBJ) + ' Got: ' + str(T))
    else:
        __CURR_OBJ = None
    uvm_field_utils_end(T)


def uvm_object_utils_begin(T):
    global __CURR_OBJ
    __CURR_OBJ = T
    uvm_object_utils(T)
    uvm_field_utils_start(T)


def uvm_object_utils_end(T):
    global __CURR_OBJ
    if __CURR_OBJ is not T:
        raise Exception('Expected: ' + str(__CURR_OBJ) + ' Got: ' + str(T))
    else:
        __CURR_OBJ = None
    uvm_field_utils_end(T)


def uvm_field_utils_start(T):
    # Create static member containers for var names and masks
    if not hasattr(T, "_m_uvm_field_names"):
        setattr(T, "_m_uvm_field_names", [])
    if not hasattr(T, "_m_uvm_field_masks"):
        setattr(T, "_m_uvm_field_masks", {})

    def _m_uvm_field_automation(self, rhs, what__, str__):
        bases = T.__bases__
        for Base in bases:
            if hasattr(Base, "_m_uvm_field_automation"):
                Base._m_uvm_field_automation(self, rhs, what__, str__)
        vals = T._m_uvm_field_names
        masks = T._m_uvm_field_masks

        T_cont = T._m_uvm_status_container
        # This part does the actual work
        if what__ == UVM_COPY:
            for v in vals:
                mask_v = masks[v]
                if not(mask_v & UVM_NOCOPY) and (mask_v & UVM_COPY != 0):
                    v_attr = getattr(rhs, v)
                    if hasattr(v_attr, "clone"):
                        setattr(self, v, v_attr.clone())
                    else:
                        setattr(self, v, v_attr)
        elif what__ == UVM_COMPARE:
            for v in vals:
                mask_v = masks[v]
                if not(mask_v & UVM_NOCOMPARE) and (mask_v & UVM_COMPARE != 0):
                    v_attr_rhs = getattr(rhs, v)
                    v_attr_self = getattr(self, v)
                    # Try simple equality first
                    if v_attr_rhs != v_attr_self:
                        if isinstance(v_attr_self, int):
                            T_cont.comparer.compare_field(v,
                                v_attr_self, v_attr_rhs, 0)
                        elif isinstance(v_attr_self, str):
                            T_cont.comparer.compare_string(v,
                                v_attr_self, v_attr_rhs, 0)
                        elif hasattr(v_attr_self, "compare"):
                            T_cont.comparer.compare_object(v,
                                v_attr_self, v_attr_rhs)

                        if (T_cont.comparer.result and
                                T_cont.comparer.show_max <= T_cont.comparer.result):
                            return
        elif what__ == UVM_PRINT:
            for v in vals:
                mask_v = masks[v]
                if not(mask_v & UVM_NOPRINT) and (mask_v & UVM_PRINT != 0):
                    v_attr_self = getattr(self, v)
                    if isinstance(v_attr_self, int):
                        T_cont.printer.print_field(v, v_attr_self,
                            sv.bits(v_attr_self), (what__ & UVM_RADIX))
                    else:
                        raise Exception("Print not implemented yet with field macros")
        elif what__ == UVM_SETINT:
            for v in vals:
                mask_v = masks[v]
                matched = False
                T_cont.scope.set_arg(v)
                matched = uvm_is_match(str__, T_cont.scope.get())
                if matched:
                    if mask_v & UVM_READONLY:
                        uvm_report_warning("RDONLY", sv.sformatf("Readonly argument match %s is ignored",
                         T_cont.get_full_scope_arg()), UVM_NONE)
                    else:
                        if T_cont.print_matches:
                            uvm_report_info("STRMTC", "set_int()" + ": Matched string "
                                + str__ + " to field " + T_cont.get_full_scope_arg(), UVM_LOW)
                    val = UVMObject._m_uvm_status_container.bitstream
                    setattr(self, v, val)
                    UVMObject.__m_uvm_status_container.status = 1
                T_cont.scope.unset_arg(v)

    setattr(T, "_m_uvm_field_automation", _m_uvm_field_automation)


def uvm_field_utils_end(T):
    pass

def uvm_field_val(name, mask):
    vals = getattr(__CURR_OBJ, "_m_uvm_field_names")
    masks = getattr(__CURR_OBJ, "_m_uvm_field_masks")
    vals.append(name)
    masks[name] = mask

def uvm_field_int(name, mask=UVM_DEFAULT):
    uvm_field_val(name, mask)

def uvm_field_string(name, mask=UVM_DEFAULT):
    uvm_field_val(name, mask)

def uvm_field_object(name, mask=UVM_DEFAULT):
    uvm_field_val(name, mask)

def uvm_field_aa(name, mask=UVM_DEFAULT):
    uvm_field_val(name, mask)

def uvm_field_aa_string_string(name, mask=UVM_DEFAULT):
    uvm_field_aa(name, mask)
