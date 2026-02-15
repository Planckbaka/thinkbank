// Package errno provides unified error handling
package errno

import (
	"fmt"

	"github.com/cloudwego/hertz/pkg/protocol/consts"
)

type ErrNo struct {
	HTTPCode int    `json:"-"`
	Code     int    `json:"code"`
	Message  string `json:"message"`
}

func (e *ErrNo) Error() string {
	return fmt.Sprintf("code=%d, message=%s", e.Code, e.Message)
}

// New creates a new error
func New(httpCode, code int, message string) *ErrNo {
	return &ErrNo{
		HTTPCode: httpCode,
		Code:     code,
		Message:  message,
	}
}

// Common errors
var (
	Success         = New(consts.StatusOK, 0, "success")
	ParamErr        = New(consts.StatusBadRequest, 10001, "invalid parameters")
	DBErr           = New(consts.StatusInternalServerError, 10002, "database error")
	RedisErr        = New(consts.StatusInternalServerError, 10003, "redis error")
	MinIOErr        = New(consts.StatusInternalServerError, 10004, "minio storage error")
	FileUploadErr   = New(consts.StatusBadRequest, 10005, "file upload failed")
	FileNotFound    = New(consts.StatusNotFound, 10006, "file not found")
	InternalErr     = New(consts.StatusInternalServerError, 10007, "internal server error")
	AssetNotFound   = New(consts.StatusNotFound, 20001, "asset not found")
	InvalidFileType = New(consts.StatusBadRequest, 20002, "invalid file type")
	FileTooLarge    = New(consts.StatusBadRequest, 20003, "file too large")
)

// ConvertErr converts error to ErrNo
func ConvertErr(err error) *ErrNo {
	if err == nil {
		return Success
	}
	if errno, ok := err.(*ErrNo); ok {
		return errno
	}
	return InternalErr
}
