import * as React from 'react';

import { C } from '../managers/Core';

import { randomId } from '../utils/Utility.js';
import Color from '../models/Color.js';


import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Close';
import PanToolAltIcon from '@mui/icons-material/PanToolAlt';
import {
  GridRowModes,
  DataGrid,
  GridToolbarContainer,
  GridActionsCellItem,
  GridRowEditStopReasons,
} from '@mui/x-data-grid';
import PropTypes from "prop-types";



function EditToolbar(props) {
  const { setRows, setRowModesModel } = props;

  EditToolbar.propTypes = {
    setRows: PropTypes.func.isRequired,
    setRowModesModel: PropTypes.func.isRequired,
  };

  const handleClick = () => {
    const id = randomId();
    setRows((oldRows) => [...oldRows, { id, locationType: '', key: '', value: '', isNew: true }]);
    setRowModesModel((oldModel) => ({
      ...oldModel,
      [id]: { mode: GridRowModes.Edit, fieldToFocus: 'locationType' },
    }));
  };

  return (
    <GridToolbarContainer>
      <Button color="primary" startIcon={<AddIcon />} onClick={handleClick}>
        Add record
      </Button>
    </GridToolbarContainer>
  );
}

export default function LocationTypeSetting({ initialRows }) {
  const [rows, setRows] = React.useState(initialRows);
  const [rowModesModel, setRowModesModel] = React.useState({});
  const [chooseRow, setChooseRow] = React.useState(null);

  LocationTypeSetting.propTypes = {
    initialRows: PropTypes.array.isRequired,
  };

  React.useEffect(() => {
    C().sourceMan.updateLocationTypes(rows);
  }, [rows]);

  React.useEffect(() => {
    return () => {
      // remove onclick event listener
      C().mapMan.removeLocationTypeOnClick();
    };
  }, []);


  const handleRowEditStop = (params, event) => {
    if (params.reason === GridRowEditStopReasons.rowFocusOut) {
      event.defaultMuiPrevented = true;
    }
  };

  const handleEditClick = (id) => () => {
    setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.Edit } });
  };

  const handleSaveClick = (id) => () => {
    setRowModesModel({ ...rowModesModel, [id]: { mode: GridRowModes.View } });
  };

  const handleDeleteClick = (id) => () => {
    setRows(rows.filter((row) => row.id !== id));
    C().mapMan.removeLocationTypeOnClick();
    C().mapMan.deleteLocationType(rows.find((row) => row.id === id).locationType);
  };

  const handleCancelClick = (id) => () => {
    setRowModesModel({
      ...rowModesModel,
      [id]: { mode: GridRowModes.View, ignoreModifications: true },
    });

    const editedRow = rows.find((row) => row.id === id);
    if (editedRow.isNew) {
      setRows(rows.filter((row) => row.id !== id));
    }
  };

  const handleChooseClick = (id) => () => {
    setChooseRow(id);
    document.body.style.cursor = 'pointer';
    // collect the location type and color of the chosen row
    const chosenRow = rows.find((row) => row.id === id);
    const locationType = chosenRow.locationType;
    const color = chosenRow.color;
    // call the map manager to set the location type and color
    C().mapMan.setLocationTypeOnClick(locationType, color);
  }

  const handleUnchooseClick = () => () => {
    setChooseRow(null);
    // call the map manager to unset the location type and color
    C().mapMan.removeLocationTypeOnClick();
  }

  const processRowUpdate = (newRow) => {
    const updatedRow = { ...newRow, isNew: false };
    const oldRow = rows.find((row) => row.id === newRow.id);
    // check if updatedRow.color changed
    if (updatedRow.color !== oldRow.color) {
      // call the map manager to update the color of the location type
      C().mapMan.updateLocationTypeColor(oldRow.locationType, updatedRow.color);
    }
    // check if updatedRow.locationType changed
    if (oldRow.locationType !== updatedRow.locationType) {
      // call the map manager to update the location type
      C().mapMan.updateLocationType(updatedRow.locationType, oldRow.locationType);
    }
    // make sure the row has a color (default to random chroma color)
    if (updatedRow.color === undefined || updatedRow.color === "") {
      const length = Color.simpleValues.length;
      updatedRow.color = Color.simpleValues[Math.floor(Math.random() * length)].name;
    }
    // make sure the row has a filter (default to empty string)
    if (updatedRow.filter === undefined) {
      updatedRow.filter = "";
    }
    // make sure the row has an uncertainty (default to 10)
    if (updatedRow.uncertainty === undefined) {
      updatedRow.uncertainty = 10;
    }

    setRows(rows.map((row) => (row.id === newRow.id ? updatedRow : row)));

    // unchoose when the row is updated
    handleUnchooseClick()();
    return updatedRow;
  };

  const handleRowModesModelChange = (newRowModesModel) => {
    setRowModesModel(newRowModesModel);
  };

  const columns = [
    { field: 'locationType', headerName: 'Location Type', width: 120, editable: true },
    { field: 'filter', headerName: 'Osm Filter', width: 250, editable: true },
    { field: 'color', headerName: 'Color', width: 80, editable: true },
    { field: 'uncertainty', headerName: 'Uncertainty', width: 100, editable: true },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 100,
      cellClassName: 'actions',
      getActions: ({ id }) => {
        const isInEditMode = rowModesModel[id]?.mode === GridRowModes.Edit;

        if (isInEditMode) {
          return [
            <GridActionsCellItem
              key={`save-${id}`}
              icon={<SaveIcon />}
              label="Save"
              sx={{
                color: 'primary.main',
              }}
              onClick={handleSaveClick(id)}
            />,
            <GridActionsCellItem
              key={`cancel-${id}`}
              icon={<CancelIcon />}
              label="Cancel"
              className="textPrimary"
              onClick={handleCancelClick(id)}
              color="inherit"
            />,
          ];
        }

        return [
          <GridActionsCellItem
            key={`edit-${id}`}
            icon={<EditIcon />}
            label="Edit"
            className="textPrimary"
            onClick={handleEditClick(id)}
            color="inherit"
          />,
          <GridActionsCellItem
            key={`delete-${id}`}
            icon={<DeleteIcon />}
            label="Delete"
            onClick={handleDeleteClick(id)}
            color="inherit"
          />,
        ];
      },
    },

    {
      field: 'choose',
      type: 'actions',
      headerName: 'Choose',
      width: 70,
      cellClassName: 'actions',
      getActions: ({ id }) => {
        const isChosen = chooseRow === id;
        if (isChosen) {
          return [
            <GridActionsCellItem
              key={`cancel-${id}`}
              icon={<CancelIcon />}
              label="Cancel"
              className="textPrimary"
              onClick={handleUnchooseClick(id)}
              color="inherit"
            />,
          ];
        }
        return [
          <GridActionsCellItem
            key={`choose-${id}`}
            icon={<PanToolAltIcon />}
            label="Choose"
            onClick={handleChooseClick(id)}
            color="inherit"
          />
        ];
      },
    }
  ];

  return (
    <Box
      sx={{
        height: 250,
        width: '100%',
        '& .actions': {
          color: 'text.secondary',
        },
        '& .textPrimary': {
          color: 'text.primary',
        },
      }}
    >
      <DataGrid
        rows={rows}
        columns={columns}
        editMode="row"
        rowModesModel={rowModesModel}
        onRowModesModelChange={handleRowModesModelChange}
        onRowEditStop={handleRowEditStop}
        processRowUpdate={processRowUpdate}
        slots={{
          toolbar: EditToolbar,
        }}
        slotProps={{
          toolbar: { setRows, setRowModesModel },
        }}
        hideFooter
      />
    </Box>
  );
}
