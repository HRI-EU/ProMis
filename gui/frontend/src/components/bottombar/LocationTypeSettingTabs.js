import { C } from '../../managers/Core'

import { Box, Grid2, IconButton, Paper, Tab, Tabs, TextField, Typography } from "@mui/material";
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';
import AddCircleOutlineOutlinedIcon from '@mui/icons-material/AddCircleOutlineOutlined';
import PanToolAltIcon from '@mui/icons-material/PanToolAlt';
import KeyboardReturnIcon from '@mui/icons-material/KeyboardReturn';
import { SliderPicker } from 'react-color'
import React from "react";
import PropTypes from 'prop-types';

function TabPanel(props) {
    const { children, value, other } = props;
    return (
        <div
            role="tabpanel"
            id={`vertical-tabpanel-${value}`}
            aria-labelledby={`vertical-tab-${value}`}
            {...other}
            >
            {(
                <Box sx={{ 
                    p: 2,
                    paddingTop: 0,
                    marginRight: 3
                }}>
                    <Grid2
                        container
                        justifyContent="flex-start"
                        spacing={2}
                    >
                        {children}
                    </Grid2>
                </Box>
            )}
        </div>
    );
}

TabPanel.propTypes = {
    children: PropTypes.node,
    value: PropTypes.number.isRequired,
    other: PropTypes.object
}

export default function LocationTypeSettingTabs() {

    const [tabState, setTabState] = React.useState(0);
    const [editMode, setEditMode] = React.useState(false);
    const [chooseMode, setChooseMode] = React.useState(false);
    const [highlight, setHighlight] = React.useState(false);

    const [color, setColor] = React.useState("#0000FF");
    const [locationType, setLocationType] = React.useState("");
    const [filter, setFilter] = React.useState("");
    const [uncertainty, setUncertainty] = React.useState(10);

    React.useEffect(() => {
        return () => {
            C().mapMan.removeLocationTypeOnClick();
            //TODOS: fix the bug which allows user to ignore duplicate location type check when in edit and unmount the component
        }
    }, [])
    

    function createTabItems() {
        let items = [];
        const locTypes = C().sourceMan.locationTypes;
        for (let i = 0; i < locTypes.length; i++) {
            const id = `vertical-tab-${i}`;
            const ariaControl = `vertical-tabpanel-${i}`;
            items.push(
                <Tab label={locTypes[i].locationType} id={id} aria-controls={ariaControl}
                    key={`tab-key-${i}`}
                    sx={{
                        textTransform: "none",
                        minHeight: 40
                    }}
                >
                </Tab>
            );
        }
        return items;
    }

    function onDelete() {
        C().sourceMan.deleteLocationTypeIndex(tabState);
        setTabState(tabState - 1); 
    }

    function isDefaultTab(i) {
        const defaultLocationType = ["UNKNOWN", "ORIGIN", "VERTIPORT"];
        return defaultLocationType.includes(C().sourceMan.locationTypes[i].locationType);
    }

    function resetEditableField(index){
        setLocationType(C().sourceMan.locationTypes[index].locationType);
        setFilter(C().sourceMan.locationTypes[index].filter);
        setColor(C().sourceMan.locationTypes[index].color);
        setUncertainty(C().sourceMan.locationTypes[index].uncertainty);
    }

    function saveable(locationType, locationTypesExcludeSelf){
        return !(locationType === "" || locationTypesExcludeSelf.map((row) => row.locationType).includes(locationType));
    }

    function onEdit() {
        if (!editMode) {
            resetEditableField(tabState);
            setEditMode(true);
            return;
        }
        const tabEntry = C().sourceMan.locationTypes[tabState];
        const oldLocationType = tabEntry.locationType;
        const oldColor = tabEntry.color;
        const oldUncertainty = tabEntry.uncertainty;
        const locationTypesExcludeSelf = C().sourceMan.locationTypes.filter((type) => type.id !== tabEntry.id);

        if (!saveable(locationType, locationTypesExcludeSelf)) {
            setHighlight(true);
            setTimeout(() => {
                setHighlight(false);
            }, 1000);
            return false;
        }

        if (oldLocationType !== locationType){
            C().mapMan.updateLocationType(locationType, oldLocationType);
        }
        if (oldColor != color) {
            C().mapMan.updateLocationTypeColor(locationType, color);
        }
        if (oldUncertainty != uncertainty) {
            C().mapMan.updateUncertainty(locationType, uncertainty);
        }
        C().sourceMan.editLocationType({
            locationType: locationType,
            filter: filter,
            color: color,
            uncertainty: uncertainty
        }, tabState);
        setEditMode(false);
        return true;
    }

    function onAddTab() {
        const index = C().sourceMan.locationTypes.length;
        C().sourceMan.addTempLocationType();
        setTabState(index);
        resetEditableField(index);
        setEditMode(true);
    }

    function onChoose() { 
        if (chooseMode) {
            C().mapMan.removeLocationTypeOnClick();
            setChooseMode(false);
            return;
        }
        const tabEntry = C().sourceMan.locationTypes[tabState];
        const locationTypeEntry = tabEntry.locationType;
        let type = "all";
        if (locationTypeEntry === "ORIGIN") {
        type = "marker";
        }
        else if (locationTypeEntry === "VERTIPORT") {
        type = "vertiport";
        }
        C().mapMan.setLocationTypeOnClick(tabEntry.locationType, tabEntry.color, tabEntry.uncertainty, type);
        setChooseMode(true);
    }

    function createTabPanels() {
        const i = tabState;
        const locTypes = C().sourceMan.locationTypes;
        return ( i > -1 ? <TabPanel value={tabState} key={`tab-panel-key-${i}`}
        >
            <Grid2
                size={12}
                container
                justifyContent="flex-start"
            >
                {!editMode && !chooseMode ? <Grid2>
                    <IconButton
                        variant="outlined"
                        sx={{
                            width: "20px",
                            height: "20px"
                        }}
                        onClick={onAddTab}
                    >
                        <AddCircleOutlineOutlinedIcon/>
                    </IconButton>
                </Grid2>: null}
                {chooseMode ? null : <Grid2>
                    <IconButton
                        variant="outlined"
                        sx={{
                            width: "20px",
                            height: "20px"
                        }}
                        onClick={onEdit}
                    >
                        { editMode ? <SaveIcon/> : <EditIcon/> }
                    </IconButton>
                </Grid2>}
                {editMode ? null:  <Grid2>
                    <IconButton
                        variant="outlined"
                        sx={{
                            width: "20px",
                            height: "20px"
                        }}
                        onClick={onChoose}
                    >
                        {chooseMode ? <KeyboardReturnIcon/> : <PanToolAltIcon />}
                    </IconButton>
                </Grid2>}
                {isDefaultTab(i) || editMode || chooseMode ? null:  <Grid2>
                    <IconButton
                        variant="outlined"
                        sx={{
                            width: "20px",
                            height: "20px"
                        }}
                        onClick={onDelete}
                    >
                        <DeleteIcon />
                    </IconButton>
                </Grid2>}
            </Grid2>
            <Grid2
                container
                id="location-type-field"
                sx={{
                    color: "white"
                }}
                justifyContent="flex-start"
                alignItems='center'
                spacing={1}
                size={6}
            >
                <Grid2
                    
                >
                    <Typography>
                        Location Type:
                    </Typography>
                </Grid2>
                <Grid2
                    
                >
                    {
                        editMode && !isDefaultTab(i) ? (
                            <TextField
                                size='small'
                                variant='outlined'
                                value={locationType}
                                onChange={(e) => setLocationType(e.target.value)}
                                sx={{
                                    width: "125px"
                                }}
                                error={highlight}
                            />
                        ) :
                        (<Typography>
                            {locTypes[i].locationType}
                        </Typography>)    
                    }
                </Grid2>
            </Grid2> 
            <Grid2
                container
                id="Filter-field"
                sx={{
                    color: "white"
                }}
                justifyContent="flex-start"
                alignItems='center'
                spacing={1}
                size={6}
            >
                <Grid2
                    
                >
                    <Typography>
                        Filter:
                    </Typography>
                </Grid2>
                <Grid2
                    
                >
                    {
                        editMode && !isDefaultTab(i) ? (
                            <TextField
                                size='small'
                                variant='outlined'
                                value={filter}
                                onChange={(e) => setFilter(e.target.value)}
                                sx={{
                                    width: "125px"
                                }}
                            />
                        ) :
                        (<Typography>
                            {locTypes[i].filter != "" ? locTypes[i].filter : "Empty"}
                        </Typography>)    
                    }
                </Grid2>
            </Grid2>
            <Grid2
                container
                id="color-field"
                sx={{
                    color: "white"
                }}
                justifyContent={'flex-start'}
                alignContent={'center'}
                spacing={1}
                size={6}
            >
                <Grid2
                    
                >
                    <Typography>
                        Color:
                    </Typography>
                </Grid2>
                <Grid2
                    container
                    justifyContent={'flex-start'}
                    alignContent={'center'}
                >
                    {
                        editMode ? 
                        (<Box
                            sx={{
                                width: "175px",
                                marginLeft: "2px"
                            }}
                        >
                            <SliderPicker
                                width='175px'
                                color={color}
                                onChange={(color) => {
                                    setColor(color.hex)
                                }}
                            />
                        </Box>) :
                        (<Paper
                            elevation={3}
                            sx={{
                                width: "20px",
                                height: "20px",
                                backgroundColor: locTypes[i].color,
                                borderStyle: "solid",
                                borderWidth: "1px",
                                borderColor: "white"
                            }}
                        >

                        </Paper>)
                    }
                    
                </Grid2>
            </Grid2>
            <Grid2
                container
                id="Uncertainty-field"
                sx={{
                    color: "white"
                }}
                justifyContent={'flex-start'}
                alignContent={'center'}
                spacing={1}
                size={6}
            >
                <Grid2
                    justifyContent={'flex-start'}
                    alignContent={'center'}
                >
                    <Typography>
                        Uncertainty:
                    </Typography>
                </Grid2>
                <Grid2
                    
                >
                    {
                        editMode ? (
                            <TextField
                                size='small'
                                variant='outlined'
                                value={uncertainty}
                                onChange={(e) => {
                                    setUncertainty(e.target.value);
                                }}
                                sx={{
                                    width: "125px"
                                }}
                            />
                        ) :
                        (<Typography>
                            {locTypes[i].uncertainty}
                        </Typography>)    
                    }
                </Grid2>
            </Grid2>
        </TabPanel> : null)
    }

    return (
        <Box
            sx={{ display: 'flex', height: 150}}
        >   
            <Tabs
                orientation="vertical"
                variant="scrollable"
                value={tabState}
                onChange={(event, newValue) => {
                    console.log("click event to new location type tab");
                    console.log(event);
                    if (editMode) {
                        if (onEdit()) {
                            setTabState(newValue);
                        }
                        return;
                    }
                    if (chooseMode) {
                        onChoose();
                    }
                    setTabState(newValue);
                }}
                sx={{
                    borderRight: 1,
                    borderColor: 'divider',
                    color: "white",
                    minWidth: 120
                }}
            >
                {
                   createTabItems()
                }
            </Tabs>
            {createTabPanels()}
        </Box>
    )
}
